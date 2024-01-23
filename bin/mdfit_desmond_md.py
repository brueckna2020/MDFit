#!/ap/rhel7/bin/python3.6

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import sys
import os
import shutil
import subprocess
import threading
import concurrent.futures
import glob
import random

#Import MDFit modules
import mdfit_prep_complex
import mdfit_run_minimization
import mdfit_get_charge
import mdfit_build_box
import mdfit_run_md
import mdfit_slicetrj

###Initiate logger###
logger = logging.getLogger(__name__)

def run_job(command):
    #Run provided command, joining list with space. Pipe stdout and sdterror to log file
    process = subprocess.run(' '.join(command), stdout=subprocess.PIPE, \
        stderr=subprocess.STDOUT, shell=True, text=True)
    
    #Iterate over sdtout and sdterror
    for line in process.stdout.split('\n'):
        #Ignore blank lines
        if line != "":
            #Ignore ExitStatus
            if "ExitStatus" not in line:
                #Write to log file for debugging
                logger.debug(line)

def random_seed():
    #Initialize random number generator 
    random.seed()

    #Return random number
    return int(random.random()*1000000)

def dircheck(master_dir):
    #Generate scratch directory name
    newdir = os.path.join(master_dir, "desmond_md", "scratch")

    #Check if scratch directory exists
    if os.path.isdir(newdir) == False:
        #If not, make scratch directory
        os.makedirs(newdir)

        #Capture current step
        logger.info("Created directory: %s"%newdir)
    
    #Scratch directory exists
    else:
        #Capture current step
        logger.info("Directory already exists: %s"%newdir)
    
    #Return scratch directory name
    return newdir

def countligs(ligpath, SCHRODINGER):
    #Check if ligand name file already exists
    if os.path.isfile("lignames.csv") == False:
        #If not, set up Schrodinger proplister variable ($SCHRODINGER/utilities/proplister)
        run_cmd = os.path.join(SCHRODINGER, 'utilities', 'proplister')

        #Set up full command
        command = [run_cmd, '-p', 'title', '-noheader', ligpath, '-c', '-o', 'lignames.csv']

        #Document current step
        logger.info("Getting lignames: %s"%' '.join(command))

        #Run job
        run_job(command)

    #Read in ligand name file
    with open("lignames.csv", 'r') as fp:

        #Get the number of ligands but counting length of file
        numligs = len(fp.readlines())

    #Document current step
    logger.info("Number of ligands: %s"%numligs)

    #Return the number of ligands for MD
    return numligs

def gen_list(num_ligs):
    #Initiate empty list
    lignum = []

    #Iterate between 0 and number of ligs
    for i in range(0, num_ligs):
        #Add to list
        lignum.append(i)

    #Return list with explicit ligand numbers
    return lignum

def prep_workers(args):
    #Check if user provided a number of workers
    if args.max_workers == 0:
        #If not, return either 32 or (number of cpu+4)
        workers = min(32, os.cpu_count() + 4)
    
    #User provided number of workers
    else:
        #Assign to variable
        workers = args.max_workers
    
    #Capture current step
    logger.info("Using %s workers for executing calls asynchronously"%workers)

    #Return number of workers
    return workers

def lig_extract(master_dir, i):
    #Read in ligand name file
    with open("lignames.csv", 'r') as infile:
        #Put all ligand names in a variable
        all_lines = infile.readlines()
    
    #Get ligand name for a given ligand number (i). Remove any trailing spaces/new line character
    ligname_base = all_lines[i].strip()

    #Return desired ligand name
    return ligname_base

def cleanup_dirs(master_dir, ligname_base, args, all_md_names):
    #Generate MD setup directory within each ligand name (desmond_md/<ligname>/md_setup)
    setup_dir = os.path.join(master_dir, "desmond_md", ligname_base, "md_setup")

    #Check if directory exists
    if os.path.isdir(setup_dir) == False:
        #If not, make directory (recursive)
        os.makedirs(setup_dir)

        #Document current step
        logger.info("Created directory: %s"%setup_dir)
    
    #Directory does not exist
    else:
        #Document current step
        logger.info("Directory already exists: %s"%setup_dir)

    #Initiate variable for iterating
    j = 0

    #Initiate empty list for temporary repetition names
    md_names = []

    #Iterate over number of repetitions
    while j < args.md_repetitions:

        #Generate repetition name using ligand name and iteration
        repname = "%s_repetition%s"%(ligname_base, j+1)

        #Append repetition name to master repetition name list
        all_md_names.append(repname)

        #Append reptition name to temporary name list
        md_names.append(repname)

        #Generate repetition directory name
        repdir = os.path.join(master_dir, "desmond_md", ligname_base, repname)

        #Check if repetition directory exists
        if os.path.isdir(repdir) == False:
            #If not, make directory (recursive)
            os.makedirs(repdir)

            #Document current step
            logger.info("Created directory: %s"%repdir)
        
        #Repetition directory exists
        else:
            #Document current step
            logger.info("Directory already exists: %s"%repdir)
        
        #Increment repetition variable
        j+=1
    
    #Return md_setup directory path and temporary reptition name list
    return setup_dir, md_names

def move_copy_files(master_dir, ligname_base, setup_dir, md_names, args, template_dir):
    #Generate list of files in desmond_md/scratch/<ligname>* to move
    searches = ("%s_*"%ligname_base, "%s.*"%ligname_base)
    move_files = []
    for each_search in searches:
        move_files.extend(glob.glob(os.path.join(master_dir, "desmond_md", "scratch", each_search)))

    #Iterate over filenames
    for file in move_files:
        #Make sure only moving setup files
        if "repetition" not in file:
            #If setup file, move to setup directory
            shutil.move(file, os.path.join(setup_dir, os.path.basename(file)))

    #Iterate over each repetition name
    for rep in md_names:
        #Copy prepared input geometry back to scratch and rename for repetition
        shutil.copy(os.path.join(setup_dir, "%s_md_setup_out.cms"%ligname_base), os.path.join(master_dir, "desmond_md", "scratch", "%s_md.cms"%rep))
        
        #Generate random number for seed for MD
        rseed = random_seed()
        
        #Check if cfg file exists
        if os.path.isfile(os.path.join(master_dir, "desmond_md", "scratch", "%s_md.cfg"%rep)) == False:
            #If not, read in template cfg file
            with open(os.path.join(template_dir, "desmond_md_job_template.cfg"), "r") as template:
                #Put all lines in a variable
                lines = template.readlines()
            
            #Open repetition-specific cfg file for writing
            with open(os.path.join(master_dir, "desmond_md", "scratch", "%s_md.cfg"%rep), "w") as ligoutput:
                #Iterate over all template lines
                for line in lines:
                    #Write to output cfg, replacing SIMTIME, RSEED, and WRITEFRQ with prepared variables (simulation time, random seed, simulation write frequency)
                    ligoutput.write(line.replace("SIMTIME",str(args.md_sim_time)).replace("RSEED",str(rseed)).replace("WRITEFRQ",str(args.md_traj_write_freq)))
        
        #Check if msj file exists
        if os.path.isfile(os.path.join(master_dir, "desmond_md", "scratch", "%s_md.msj"%rep)) == False:
            #If not, read in template msj file
            with open(os.path.join(template_dir, "desmond_md_job_template.msj"), "r") as template:
                #Put all lines in a variable
                msjlines = template.readlines()
            
            #Open repetition-specific msj file for writing
            with open(os.path.join(master_dir, "desmond_md", "scratch", "%s_md.msj"%rep), "w") as ligoutput:
                #Iterate over all template lines
                for msjline in msjlines:
                    #Write to output msj, replacing CONFIG_NAME (repetition-specific cfg filename)
                    ligoutput.write(msjline.replace("CONFIG_NAME","%s_md.cfg"%rep))

def rep_one_setup(SCHRODINGER, ligpath, i, master_dir, args, bmin_host, multisim_host, all_md_names, template_dir):
    #Extract specific ligand from ligand library and get ligand base name
    ligname_base = lig_extract(master_dir, i)

    #Complex protein and ligand. Calls mdfit_prep_complex.py
    pvcomplex = mdfit_prep_complex.main(SCHRODINGER, ligpath, ligname_base, i, master_dir, args)

    #Minimize prepared complex. Calls mdfit_run_minimization.py
    bmincomplex = mdfit_run_minimization.main(ligname_base, pvcomplex, args, bmin_host, SCHRODINGER, master_dir, template_dir)

    #Calculate the total charge of the system. Calls mdfit_get_charge.py
    charge = mdfit_get_charge.main(SCHRODINGER, ligname_base, master_dir, args)

    #Neutralizes and solvates the minimized protein and ligand complex. Calls mdfit_build_box.py
    simbox = mdfit_build_box.main(master_dir, SCHRODINGER, args, charge, ligname_base, multisim_host, bmincomplex, template_dir)

    #Blocks multiple threads writing to file at the same time
    with threading.Lock():
        #Move MD setup files to permanent directory. Generate permanent directory name and get all repetition names
        setup_dir, md_names = cleanup_dirs(master_dir, ligname_base, args, all_md_names)

    #Prepares repetition-specfic input files for MD (cfg/msj files)
    move_copy_files(master_dir, ligname_base, setup_dir, md_names, args, template_dir)

    #Return ligand base name
    return ligname_base

def move_trj_files(master_dir, lig, lig_basename):
    #Get list of all files in desmond_md/scratch/<ligname>* to move
    move_files = glob.glob(os.path.join(master_dir, "desmond_md", "scratch", "%s*"%lig))
    
    #Iterate over all files in list
    for file in move_files:
        #Make sure only moving repetition files
        if "repetition" in file:
            #If repetition-specific file, check if already exists
            if os.path.isfile(os.path.join(master_dir, "desmond_md", lig_basename, lig, os.path.basename(file))) == True:
                #Remove file/directory
                os.remove(os.path.join(master_dir, "desmond_md", lig_basename, lig, os.path.basename(file)))
            elif os.path.isdir(os.path.join(master_dir, "desmond_md", lig_basename, lig, os.path.basename(file))) == True:
                shutil.rmtree(os.path.join(master_dir, "desmond_md", lig_basename, lig, os.path.basename(file)))
            
            #Copy to permanent location
            shutil.move(file, os.path.join(master_dir, "desmond_md", lig_basename, lig, os.path.basename(file)))

def md_production(SCHRODINGER, master_dir, args, desmond_host, lig):
    #Run Desmond MD. Generate output trajectory filenames and ligand basename for future use. Calls mdfit_run_md.py
    outcms, outtrj, lig_basename = mdfit_run_md.main(lig, args, desmond_host, SCHRODINGER, master_dir)

    #Slice trajectory (remove frames). Calls mdfit_slicetrj.py
    sliced_trj = mdfit_slicetrj.main(SCHRODINGER, lig, master_dir, args)

    #Move Desmond MD trajectory files to permanent directory
    move_trj_files(master_dir, lig, lig_basename)

    #Return output trajectory filenames
    return outcms, outtrj

def main(args, master_dir, ligfileprefix, SCHRODINGER, ligpath, template_dir, inst_params):
    ###TODO: check if lignames are unique

    #Check if user wants Desmond MD
    if args.skip_md == True:
        #If not, capture current step
        logger.info("Skipping Desmond MD (--skip_md provided by user)")
    
    #User wants Desmond MD
    else:
        #Generate scratch directory for running jobs
        scratch_dir = dircheck(master_dir)

        #Capture current step
        logger.info("Changing directory to %s"%scratch_dir)

        #Change to scratch directory
        os.chdir(scratch_dir)

        #Prep minimization host
        bmin_host = inst_params["hostnames"]["BMIN"]

        #Document current step
        logger.debug("Minimization hostname is %s"%bmin_host)

        #Prep multisim host
        multisim_host = inst_params["hostnames"]["MULTISIM"]

        #Document current step
        logger.debug("Multisim hostname is %s"%multisim_host)

        #Prep hostname for Desmond
        desmond_host = inst_params["hostnames"]["DESMOND"]

        #Document current step
        logger.debug("Desmond hostname is %s"%desmond_host)

        #Get number of ligs for parallelization
        num_ligs = countligs(ligpath, SCHRODINGER)

        #Generate a list with ligand numbers [0, 1, 2, ...]
        lignum = gen_list(num_ligs)

        #Prepare number of workers based on ThreadPoolExecutor suggestion
        workers = prep_workers(args)

        #Initiate list to capture names for MD jobs
        all_md_names = []

        #Start parallel task controller
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            #Run MD setup asynchronously
            setup_jobs = {executor.submit(rep_one_setup, SCHRODINGER, ligpath, lig, master_dir, args, bmin_host, multisim_host, all_md_names, template_dir): lig for lig in lignum}

            #For each asynchronous job
            for future in concurrent.futures.as_completed(setup_jobs):
                #Capture the output
                lig = setup_jobs[future]

                #Try getting the ligname
                try:
                    ligname_base = future.result()
                
                #If a step in MD setup fails
                except Exception as exc:
                    #Capture error
                    logger.critical("An exception occurred during MD setup: %s"%(exc))

                    #Exit
                    sys.exit()
                
                #Otherwise, MD setup was successful
                else:
                    #Capture current step
                    logger.info("Setup success: %s"%(ligname_base))
        
        #Capture current step
        logger.info("MD setup complete. Launching %s production jobs."%len(all_md_names))

        #Start parallel task controller
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            #Run MD asynchronously
            prod_jobs = {executor.submit(md_production, SCHRODINGER, master_dir, args, desmond_host, lig): lig for lig in all_md_names}

            #For each asynchronous job
            for future in concurrent.futures.as_completed(prod_jobs):
                #Capture the output
                lig = prod_jobs[future]

                #Try getting the trajectory names
                try:
                    outcms, outtrj = future.result()

                #If a step in MD fails
                except Exception as exc:
                    #Capture error
                    logger.critical("%s generated an exception during production MD: %s"%(outcms, exc))

                    #Exit
                    sys.exit()
                
                #Otherwise, MD was successful
                else:
                    #Capture current step
                    logger.info("Production success: %s, %s"%(outcms, outtrj))

    #Capture current step
    logger.info("Changing directory to %s"%master_dir)

    #Change to master directory
    os.chdir(master_dir)

if __name__ == '__main__':
    main(args, master_dir, ligfileprefix, SCHRODINGER, ligpath, template_dir, inst_params)