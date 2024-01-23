#!/ap/rhel7/bin/python3.6

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import sys
import os
import subprocess

#Import Schrodinger modules
from schrodinger.application.desmond.packages import traj

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

def count_frames(trj_path):
    #Read in trajectory with Schrodinger's read_traj utilty
    tr = traj.read_traj(trj_path)

    #Return length of trajectory (number of frames)
    return len(tr)

def main(SCHRODINGER, rep, master_dir, args):
    #Prepare Schrodinger's run command ($SCHRODINGER/run)
    run_cmd = os.path.join(SCHRODINGER, 'run')

    #Generate repetition name <ligname>_repetition<#>
    basename = os.path.basename(rep)

    #Generate ligand name <ligname>
    ligbase = basename.split("_repetition")[0]

    #Generate path to trajectory files in scratch space
    md_path = os.path.join(master_dir, "desmond_md", "scratch")

    #Check if trajectory files are in scratch
    if os.path.isfile(os.path.join(md_path, "%s-out.cms"%basename)) == True:
        #If they are, generate path to trajectory file in scratch space
        cms_path = os.path.join(md_path, "%s-out.cms"%basename)

        #If they are, generate path to trajectory directory in scratch space
        trj_path = os.path.join(md_path, "%s_trj"%basename)
    
    #Trajectory files are in permanent directories; allows slice to be done separate from Desmond MD
    else:
        #Generate path to trajectory file in permanent directory
        cms_path = os.path.join(master_dir, "desmond_md", ligbase, basename, "%s-out.cms"%basename)
        #Generate path to trajectory directory in permanent directory
        trj_path = os.path.join(master_dir, "desmond_md", ligbase, basename, "%s_trj"%basename)

    #Check if the user wants to remove frames
    if args.slice_start != 0 or args.slice_end != None:
        #Slice hasn't been done before
        if os.path.isfile(os.path.join(master_dir, "desmond_md", ligbase, basename, "%s_sliced-out.cms"%basename)) == False:
            #Get total number of frames in trajectory
            total_frames = count_frames(trj_path)

            #Check if user wants to remove frames from end of trajectory
            if args.slice_end == None:
                #If not, set variable to total number of frames
                args.slice_end = total_frames

            #Prepare slice command
            trj_slice = [run_cmd, "trj_merge.py", "-s", "%s:%s:1"%(args.slice_start, args.slice_end), "-o", "%s_sliced"%basename, cms_path, trj_path]

            #Capture current step
            logger.info("Removing frames from trajectory: %s"%' '.join(trj_slice))

            #Run trajectory slicing
            run_job(trj_slice)
    
        #Slice has been done before
        else:
            #Capture current step
            logger.info("Sliced trajectory already found. Skipping slice.")
    
    #No slice desired
    else:
        #Capture current step
        logger.info("Not removing frames from trajectory")

if __name__ == '__main__':
    main(SCHRODINGER, rep, master_dir, args)