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
import time
import tarfile
import glob

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

def prep_hostname(args, inst_params):
    #Add job-server prefix to host and append number of processors
    hostname = inst_params["hostnames"]["FFBUILDER"]
    processors = inst_params["parameters"]["FFPROC"]
    host = "%s:%s"%(hostname, processors)

    #Document current step
    logger.info("FFBuilder hostname is %s"%host)

    #Return prepared hostname
    return host


def dircheck(master_dir):
    #Generate path to FFBuilder directory
    newdir = os.path.join(master_dir, "ffbuilder")

    #Check if FFBuilder directory already exists
    if os.path.isdir(newdir) == False:
        #If not, make directory
        os.mkdir(newdir)

        #Document current step
        logger.info("Created directory: %s"%newdir)

    #FFBuilder directory already exists
    else:
        #Get current date and time in a string
        timestr = time.strftime("%Y%m%d-%H%M%S")

        #Generate temporary directory name
        tmpfile = "ffbuilder_%s"%timestr

        #Move old FFBuilder directory to temporary directory
        os.rename(newdir, tmpfile)

        #Generate a tar directory name
        tarfilename = "%s.tar.gz"%tmpfile

        #Document current step
        logger.info("Directory found. Archiving to %s"%tarfilename)

        #Tar/compress old FFBuilder directory
        with tarfile.open(tarfilename, "w:gz") as tar:
            tar.add(tmpfile)

        #Delete (recursive) old FFBuilder directory
        shutil.rmtree(tmpfile)

        #Re-create empty FFBuilder directory
        os.mkdir(newdir)

    #Document current step
    logger.info("Changing directory to %s"%newdir)

    #Change to FFBuilder directory
    os.chdir(newdir)

    #Return FFBuilder directory name
    return newdir

def gen_opls(args, schrodinger_version):
    #Change sub-version to underscore to comply with FFBuilder formatting
    version = schrodinger_version.replace("-", "_")

    #Generate name for force field file
    forcefieldfile = "custom_%s.opls"%version

    #Generate full path to force field file
    forcefieldfilepath = os.path.join(args.oplsdir, forcefieldfile)

    #Return force field file name and full path
    return forcefieldfile, forcefieldfilepath

def ffbuilder(forcefieldfilepath, SCHRODINGER, ligfileprefix, ligpath, newdir, forcefieldfile, args, host):
    #Prepare Schrodinger run command ($SCHRODINGER/ffbuilder)
    run_cmd = os.path.join(SCHRODINGER, 'ffbuilder')

    #Generate jobname using ligand file name
    jobname = "MDFit_%s"%ligfileprefix

    #Generate path to output opls file for FFBuilder
    outopls = os.path.join(newdir, "%s_oplsdir"%jobname, forcefieldfile)

    #Check if custom force field file already exists
    if os.path.isfile(forcefieldfilepath) == False:
        #If not, capture current step
        logger.info("Custom force-field does not exist. Creating one.")

        #Check if oplsdir exists
        if os.path.isdir(os.path.join(args.oplsdir)) == False:
            #Make directories (recursive) to custom force field file
            os.makedirs(os.path.dirname(forcefieldfilepath))

        #Prepare FFBuilder command
        command = [run_cmd, '-HOST', host, '-JOBNAME', jobname, ligpath, '-WAIT']
    
    #Custom force field file exists
    else:
        #Capture current step
        logger.info("Custom force-field found. Merging new parameters with custom force-field.")

        #Prepare FFBuilder command
        command = [run_cmd, '-HOST', host, '-JOBNAME', jobname, '-OPLSDIR', forcefieldfilepath, ligpath, '-WAIT']
    
    #Capture current step
    logger.info("Running FFBuilder: %s"%' '.join(command))

    #Run FFBuilder
    run_job(command)

    #Return path to output opls file
    return outopls

def FFcleanup(forcefieldfilepath, forcefieldfile, homepath, outopls, SCHRODINGER):
    #Check if custom force field file already exists. If not, copy generated file to new oplsdir
    if os.path.isfile(forcefieldfilepath) == False:
        #Generate path to home oplsdir
        home_oplsdir = os.path.join(homepath, ".schrodinger", "opls_dir")

        #Get any custom opls files
        opls_files = glob.glob(os.path.join(home_oplsdir, "custom_*.opls"))

        #Try copying FFBuilder output file to custom force field path
        if os.path.isfile(outopls) == True:
            #If file was generated, capture current step
            logger.info("Copying custom OPLS to oplsdir: %s"%outopls)
            logger.info("                              : %s"%forcefieldfilepath)

            #Copy custom force field to user-specified oplsdir
            shutil.copy(outopls,forcefieldfilepath)
        
            #This fails if custom force field file does not exist and FFBuilder did not generate new parameters. Try finding custom opls file in $HOME
        
        #Check if current release force field file exists in default location
        elif os.path.isfile(os.path.join(home_oplsdir, forcefieldfile)) == True:
            #Capture current step
            logger.info("No new parameters generated. Copying opls file from %s"%home_oplsdir)

            #Copy file
            shutil.copy(os.path.join(home_oplsdir, forcefieldfile),forcefieldfilepath)

        #See if older version exists in $HOME
        elif opls_files != []:
            #Prepare Schrodinger custom_params utiltiy
            custom_params = os.path.join(SCHRODINGER, "utilities", "custom_params")

            #Prepare command for upgrading custom parameters
            command = [custom_params, "upgrade", home_oplsdir]

            #Capture current step
            logger.info("Upgrading custom parameters: %s"%' '.join(command))

            #Run upgrade
            run_job(command)

            #Capture current step
            logger.info("Copying upgraded custom parameters to desired oplsdir")
            
            #Copy upgraded opls file
            shutil.copy(os.path.join(home_oplsdir, forcefieldfile),forcefieldfilepath)

        else:
            #Capture error and provide some work-around
            logger.critical("Force field file creation failed and default opls could not be located. Workaround: copy default opls file to the desired --oplsdir and rerun MDFit.")

            #Exit
            sys.exit()

def main(args, master_dir, SCHRODINGER, ligpath, ligfileprefix, schrodinger_version, inst_params, homepath):
    #Check if user wants to skip FFBuilder
    if args.skip_ff == True:
        #If true, document current step
        logger.info("Skipping FFBuilder (--skip_ff provided by user)")
    
    #User wants FFBuilder
    else:
        #Prepare hostname format
        host = prep_hostname(args, inst_params)

        #Generate FFBuilder directory
        newdir = dircheck(master_dir)

        #Generate FFBuilder output filename
        forcefieldfile, forcefieldfilepath = gen_opls(args, schrodinger_version)

        #Run FFBuilder
        outopls = ffbuilder(forcefieldfilepath, SCHRODINGER, ligfileprefix, ligpath, newdir, forcefieldfile, args, host)

        #Move custom parameters to user-specified oplsdir
        FFcleanup(forcefieldfilepath, forcefieldfile, homepath, outopls, SCHRODINGER)

    #Document current step
    logger.info("Changing directory to %s"%master_dir)

    #Change back to master directory
    os.chdir(master_dir)

if __name__ == '__main__':
    main(args, master_dir, SCHRODINGER, ligpath, ligfileprefix, schrodinger_version, inst_params, homepath)
