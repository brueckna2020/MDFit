#!/ap/rhel7/bin/python3.6

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import os
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

def main(ligname, args, desmond_host, SCHRODINGER, master_dir):
    #Generate trajectory file name
    outcms = "%s-out.cms"%ligname

    #Generate trajectory directory name
    outtrj = "%s_trj"%ligname

    #Get base ligand name <ligand>
    lig_basename = ligname.split("_repetition")[0]

    #Check if trajectory file and directory exist
    if os.path.isfile(os.path.join(master_dir, "desmond_md", lig_basename, ligname, outcms)) == False or os.path.isdir(os.path.join(master_dir, "desmond_md", lig_basename, ligname, outtrj)) == False:
        #If not, prepare Schrodinger's multisim command ($SCHRODINGER/utilities/multisim)
        run_cmd = os.path.join(SCHRODINGER, "utilities", "multisim")

        #Prepare Desmond MD command
        command = [run_cmd, '-JOBNAME', ligname, '-HOST', desmond_host, '-maxjob', '1', '-cpu', '1', '-m', '%s_md.msj'%ligname, '-c', '%s_md.cfg'%ligname, '-description', '"Molecular Dynamics"', '%s_md.cms'%ligname, '-mode', 'umbrella', '-set', '"stage[1].set_family.md.jlaunch_opt=[\"-gpu\"]"', '-o', outcms, '-OPLSDIR', args.oplsdir, '-lic', 'DESMOND_GPGPU:16', '-ATTACHED', '-WAIT']
        
        #Capture current step
        logger.info("Running Desmond: %s"%' '.join(command))

        #Run Desmond MD
        run_job(command)

    #Trajectory file(s) exist
    else:
        #Capture current step
        logger.info("Desmond trajectory found: %s, %s"%(outcms, outtrj))
    
    #Return trajectory file and directory names and ligand name
    return outcms, outtrj, lig_basename

if __name__ == '__main__':
    main(ligname, args, desmond_host, SCHRODINGER, master_dir)