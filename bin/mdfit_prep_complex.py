#!/ap/rhel7/bin/python3.6

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import os
import shutil
import subprocess

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

def main(SCHRODINGER, ligpath, ligname, i, master_dir, args):
    #Prepare Schrodinger's structure subset command ($SCHRODINGER/utilities/structsubset)
    run_cmd = os.path.join(SCHRODINGER, 'utilities', 'structsubset')

    #Prepare Schrodinger's structure concatination command ($SCHRODINGER/utilities/structcat)
    structcat = os.path.join(SCHRODINGER, 'utilities', 'structcat')

    #Prepare Schrodinger's structure run command ($SCHRODINGER/run)
    schrun = os.path.join(SCHRODINGER, 'run')

    #Generate pose viewer filename
    pvcomplex = "%s_pv.mae"%ligname

    #Generate complex output filename
    outname = "%s_out_complex.mae"%ligname

    #Check if pose viewer file exists
    if os.path.isfile(os.path.join(master_dir, "desmond_md", ligname, "md_setup", pvcomplex)) == False:
        #If not, check if ligand sdf file exists and ligands are not precomplexed with protein
        if os.path.isfile("%s.sdf"%ligname) == False and not args.precomplex:
            #If not, prepare structure subset command (extract ligand from library)
            command = [run_cmd, '-n', str(i+1), ligpath, '%s.sdf'%ligname]

            #Document current step
            logger.info("Getting ligand: %s"%' '.join(command))

            #Run structure subset (extract ligand from library)
            run_job(command)
        
        #Ligands are precomplexed with protein
        else:
            #If not, prepare structure subset command (extract ligand from library)
            command = [run_cmd, '-n', str(i+1), ligpath, '%s.mae'%ligname]

            #Document current step
            logger.info("Getting ligand: %s"%' '.join(command))

            #Run structure subset (extract ligand from library)
            run_job(command)
        

        #Check if protein and ligand are pre-complexed
        if not args.precomplex:
            #If not, generate path to protein file
            protein_path = os.path.join(master_dir, args.prot)

            #Prepare structure concatination command (combine protein and ligand files)
            command1 = [structcat, "-i", protein_path, "%s.sdf"%ligname, "-o", pvcomplex]
            
            #Capture current step
            logger.info("Complexing protein and ligand: %s"%' '.join(command1))
            
            #Prepare pose viewer command
            command2 = [schrun, "pv_convert.py", "-mode", "merge", pvcomplex]

            #Capture current step
            logger.info("Merging protein and ligand: %s"%' '.join(command2))
            
            #Run concatination command
            run_job(command1)

            #Run pose viewer command
            run_job(command2)

            #Rename auto-generated output complex name to desired filename ("-out" > "_out")
            os.rename("%s-out_complex.mae"%ligname,outname)
        
        #Protein and ligand are pre-complexed
        else:
            #Prepare structure concatination command (translate sdf to mae)
            command1 = [structcat, "-i", "%s.mae"%ligname, "-o", pvcomplex]

            #Capture current step
            logger.info("Complexing protein and ligand: %s"%' '.join(command1))

            #Prepare pose viewer command
            command2 = [schrun, "pv_convert.py", "-mode", "merge", pvcomplex]

            #Capture current step
            logger.info("Merging protein and ligand: %s"%' '.join(command2))

            #Run concatination command
            run_job(command1)

            #Run pose viewer command
            run_job(command2)

            #Copy pose viewer complex to desired filename
            shutil.copy(pvcomplex,outname)
    
    #Pose viewer file exists
    else:
        #Capture current step
        logger.info("Complex file found: %s"%pvcomplex)

    #Return pose viewer filename
    return pvcomplex

if __name__ == '__main__':
    main(SCHRODINGER, ligpath, ligname, i, master_dir, args)