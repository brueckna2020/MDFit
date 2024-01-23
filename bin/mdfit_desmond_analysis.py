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
import glob
import concurrent.futures

#Import MDFit modules
import mdfit_event_analysis
import mdfit_extract_dat
import mdfit_combine_csvs
import mdfit_cluster_traj

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

def dircheck(master_dir):
    #Generate scratch directory name
    newdir = os.path.join(master_dir, "desmond_md_analysis", "scratch")

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

    #Document current step
    logger.info("Changing directory to %s"%newdir)

    #Change to scratch directory
    os.chdir(newdir)

    #Return scratch directory name
    return newdir

def ligfile_check(master_dir, args):
    #Check if user wants to analyze all ligands
    if args.analysis_lig == "all":
        #If they do, generate list with paths to all repetition directories
        reppaths = glob.glob(os.path.join(master_dir, "desmond_md", "*", "*repetition*"))
    
    #TODO: accept list of ligands for analysis
    #Otherwise, user wants single ligand analysis
    else:
        #Assign list with path to single repetition directory
        reppaths = [os.path.join(master_dir, "desmond_md", "*", "*%s*"%args.analysis_lig)]

    #Return list of paths to repeptition directories
    return reppaths

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

def run_analysis(SCHRODINGER, rep, master_dir, args, inst_params):
    #Analyze given trajectory. Call mdfit_event_analysis.py
    event_analysis_command2 = mdfit_event_analysis.main(SCHRODINGER, rep, master_dir, args, inst_params)

    #Return command for serial job
    return event_analysis_command2

def dat_extract(pdf_commands):
    #Iterate over all dat extract commands
    for command in pdf_commands:
        #Check if commands were generated. Can be empty if previous eaf files are found
        if command != []:
            #Capture current step
            logger.info("Generating data files: %s"%' '.join(command))

            #Run each job serially
            run_job(command)

def tabulate_simfp(SCHRODINGER, rep, master_dir, args):
    #Tabulate SimFP and compatibility data. Calls mdfit_extract_dat.py
    mdfit_extract_dat.main(SCHRODINGER, rep, master_dir, args)

    #Check if clustering will happen
    if args.skip_cluster == True:
        #If skipping, do cleanup now
        cleanup(rep, master_dir, args)

def combine_csvs(master_dir):
    #Combine all tabulated ligand-specific SimFPs and compatibility files into master file (serial)
    #Call mdfit_combine_csvs.py
    mdfit_combine_csvs.main(master_dir)

def cleanup(rep, master_dir, args):
    #Generate ligand name <ligname>-repetition<#>
    basename = os.path.basename(rep)

    #Generate base ligand name <ligname>
    ligbase = basename.split("_repetition")[0]

    #Generate path to repetition directory desmond_md_analysis/<ligname>/<ligname>-repetition<#>
    repdir = os.path.join(master_dir, "desmond_md_analysis", ligbase, basename)
    
    #Check if reptition directory exists
    if os.path.isdir(repdir) == False:
        #If not, make directory (recursive)
        os.makedirs(repdir)

        #Capture current step
        logger.info("Created directory: %s"%repdir)

    #Directory exists
    else:
        #Capture current step
        logger.info("Directory already exists: %s"%repdir)

    #Generate list of paths for files to move from desmond_md_analysis/scratch/<ligname>*
    searches = ("%s_*"%basename, "%s.*"%basename)
    move_files = []
    for each_search in searches:
        move_files.extend(glob.glob(os.path.join(master_dir, "desmond_md_analysis", "scratch", each_search)))

    #Iterate over list of file paths
    for file in move_files:
        #Move to repetition directory
        shutil.move(file, os.path.join(repdir, os.path.basename(file)))

def cluster_traj(SCHRODINGER, rep, master_dir, args):
    #Cluster trajectories. Calls mdfit_cluster_traj.py
    mdfit_cluster_traj.main(SCHRODINGER, rep, master_dir, args)

    #Move files from scratch to repetition directories
    cleanup(rep, master_dir, args)

def main(args, master_dir, SCHRODINGER, inst_params):
    #Generate scratch directory
    scratch_dir = dircheck(master_dir)

    #Check that user wants analysis
    if args.skip_analysis == False:
        #If they do, get paths to all the repetition files
        reppaths = ligfile_check(master_dir, args)

        #Prepare number of workers based on ThreadPoolExecutor suggestion
        workers = prep_workers(args)

        #Initiate empty list for final dat and png file extraction. Has to be run serially
        pdf_commands = []

        #Start parallel task controller
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            #Run MD analysis asynchronously
            analysis_jobs = {executor.submit(run_analysis, SCHRODINGER, rep, master_dir, args, inst_params): rep for rep in reppaths}

            #For each asynchronous job
            for future in concurrent.futures.as_completed(analysis_jobs):
                #Capture the output
                lig = analysis_jobs[future]

                #Try getting the serial command
                try:
                    pdf_commands.append(future.result())

                #If a step in MD analysis fails
                except Exception as exc:
                    #Capture error
                    logger.critical("%s generated an exception during event analysis: %s"%(lig, exc))

                    #Exit
                    sys.exit()

                #Otherwise, MD analysis was successful
                else:
                    #Capture current step
                    logger.info("Analysis success: %s"%(lig))

        #Capture current step
        logger.info("Extracting dat and png files serially")

        #Limitation of Schrodinger's utility. Cannot control output filenames. Forced to run dat extraction serially.
        dat_extract(pdf_commands)

        #Start parallel task controller
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            #Run MD analysis tabulation asynchronously
            tabulate_jobs = {executor.submit(tabulate_simfp, SCHRODINGER, rep, master_dir, args): rep for rep in reppaths}
            
            #For each asynchronous job
            for future in concurrent.futures.as_completed(tabulate_jobs):
                #Capture the output
                lig = tabulate_jobs[future]
                
                #Try getting returned data
                try:
                    data = future.result()

                #If a step in MD analysis tabulation fails
                except Exception as exc:
                    #Capture error
                    logger.critical("%s generated an exception during tabulation: %s"%(lig, exc))

                    #Exit
                    sys.exit()
                
                #Otherwise, MD analysis tabulation was successful
                else:
                    #Capture current step
                    logger.info("Trj extraction success: %s"%(lig))
        
        #Combine all SimFP and compatibility CSV files into a master file. Must be serial
        combine_csvs(master_dir)

        #Check if the user wants to cluster the trajectories
        if args.skip_cluster == True:
            #If true, document current step
            logger.info("Skipping trajectory clustering (--skip_cluster provided by user)")
    
        #User wants clustering
        else:
            #If they do, start parallel task controller
            with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
                #Run MD trajectory clustering asynchronously
                cluster_jobs = {executor.submit(cluster_traj, SCHRODINGER, rep, master_dir, args): rep for rep in reppaths}

                #For each asynchronous job
                for future in concurrent.futures.as_completed(cluster_jobs):
                    #Capture the output
                    lig = cluster_jobs[future]

                    #Try getting returned data
                    try:
                        data = future.result()

                    #If a step in MD trajectory clustering fails
                    except Exception as exc:
                        #Capture the error
                        logger.critical("%s generated an exception during clustering: %s"%(lig, exc))

                        #Exit
                        sys.exit()
                    
                    #Otherwise, MD trajectory clustering was successful
                    else:
                        #Capture current step
                        logger.info("Clustering success: %s"%(lig))

    #Capture current step
    logger.info("Changing directory to %s"%master_dir)

    #Change to master directory
    os.chdir(master_dir)

if __name__ == '__main__':
    main(args, master_dir, SCHRODINGER, inst_params)