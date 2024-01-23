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

#Fixes issue with X11 forwarding
os.environ['QT_QPA_PLATFORM']='offscreen'

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

def dircheck(master_dir, basename):
    #Generate directory name in scratch space for each ligand <ligname>-repetition<#>
    newdir = os.path.join(master_dir, "desmond_md_analysis", "scratch", basename)

    #Check if directory exists
    if os.path.isdir(newdir) == False:
        #If not, make directory (recursive)
        os.makedirs(newdir)

        #Capture current step
        logger.info("Created directory: %s"%newdir)

    #Directory exists
    else:
        #Capture current step
        logger.info("Directory already exists: %s"%newdir)
    
    #Return ligand scratch directory path
    return newdir

def trj_pathnames(md_path, basename):
    #Check if slice trajectory exists
    if os.path.isfile(os.path.join(md_path, "%s_sliced-out.cms"%basename)) == True:
        #If it does, set cms path to sliced trajectory file
        cms_path = os.path.join(md_path, "%s_sliced-out.cms"%basename)

        #If it does, set trj path to sliced trajectory directory
        trj_path = os.path.join(md_path, "%s_sliced_trj"%basename)
    
    #Check if unsliced trajectory does and sliced trajectory does not exist
    elif os.path.isfile(os.path.join(md_path, "%s_sliced-out.cms"%basename)) == False and os.path.isfile(os.path.join(md_path, "%s-out.cms"%basename)) == True:
        #If it does, set cms path to unsliced trajectory file
        cms_path = os.path.join(md_path, "%s-out.cms"%basename)

        #If it does, set trj path to unsliced trajectory file
        trj_path = os.path.join(md_path, "%s_trj"%basename)
    
    #Could not locate trajectory
    else:
        #Log error
        logger.critical("Trajectory could not be located!")

        #Exit
        sys.exit()

    #Return paths to trajectory files
    return cms_path, trj_path

def gen_outname(basename):
    #Generate input eaf filename
    eaf_in = "%s-in.eaf"%basename

    #Generate output eaf filename
    eaf_out = "%s-out.eaf"%basename

    #Generate output pdf filename
    eaf_pdf = "%s_analysis.pdf"%basename

    #Return generated filenames
    return eaf_in, eaf_out, eaf_pdf


def main(SCHRODINGER, rep, master_dir, args, inst_params):
    #Prepare analysis hostname
    analysis_host = inst_params["hostnames"]["ANALYSIS"]
    
    #Prepare Schrodinger run command ($SCHRODINGER/run)
    run_cmd = os.path.join(SCHRODINGER, 'run')

    #Get repetition name <ligname>-repetition<#>
    basename = os.path.basename(rep)

    #Get ligand name <ligname>
    ligbase = basename.split("_repetition")[0]
    
    #Generate pathname to trajectory files
    md_path = os.path.join(master_dir, "desmond_md", ligbase, basename)

    #Generate paths to trajectory files
    cms_path, trj_path = trj_pathnames(md_path, basename)

    #Generate filenames for event analysis
    eaf_in, eaf_out, eaf_pdf = gen_outname(basename)

    #Check if output eaf file exists in scratch and permanent space
    if os.path.isfile(os.path.join(master_dir, "desmond_md_analysis", "scratch", eaf_out)) == False and os.path.isfile(os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, eaf_out)) == False:
        #If not, prepare directory for text data and plot files
        data_dir = dircheck(master_dir, basename)

        #Need to wrap ASL in double quotes for Schrodinger to interpret
        prot_ASL = '"%s"'%args.prot_ASL
        lig_ASL = '"%s"'%args.lig_ASL

        #Prepare event analysis (analyze) command
        event_analysis_command1 = [run_cmd, "event_analysis.py", "analyze", cms_path, "-p", prot_ASL, "-l", lig_ASL, "-out", basename]

        #Prepare simulation analysis command
        analyze_simulation_command=[run_cmd, "analyze_simulation.py", "-HOST", analysis_host, "-OPLSDIR", args.oplsdir, "-JOBNAME", basename, "-WAIT", cms_path, trj_path, eaf_out, eaf_in]

        #Prepare event analysis (report) command
        event_analysis_command2=[run_cmd, "event_analysis.py", "report", "-pdf", eaf_pdf, "-data", "-plots", "-data_dir", data_dir, eaf_out]

        #Capture current step
        logger.info("Generating eaf file: %s"%' '.join(event_analysis_command1))

        #Run event analysis (analyze) command
        run_job(event_analysis_command1)

        #Capture current step
        logger.info("Running simulation analysis: %s"%' '.join(analyze_simulation_command))

        #Run simulation analysis command
        run_job(analyze_simulation_command)

        #Limitation of Schrodinger's code. Cannot control output filenames and asynchronous calls clash. Forced to run serially.
        #Return event analysis (report) command
        return event_analysis_command2

    #Output eaf file exists
    else:
        #Check if PDF was generated
        if os.path.isfile(os.path.join(master_dir, "desmond_md_analysis", "scratch", eaf_pdf)) == False and os.path.isfile(os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, eaf_pdf)) == False:
            #If not, prepare directory for text data and plot files
            data_dir = dircheck(master_dir, basename)

            #Prepare event analysis (report) command
            event_analysis_command2=[run_cmd, "event_analysis.py", "report", "-pdf", eaf_pdf, "-data", "-plots", "-data_dir", data_dir, eaf_out]

            #Limitation of Schrodinger's code. Cannot control output filenames and asynchronous calls clash. Forced to run serially.
            #Return event analysis (report) command
            return event_analysis_command2
        
        #PDF was generated
        else:
            #Capture current step
            logger.info("eaf file found. Skipping event analysis.")

            #Return empty list - event analysis (report) not necessary
            return []

if __name__ == '__main__':
    main(SCHRODINGER, rep, master_dir, args, inst_params)