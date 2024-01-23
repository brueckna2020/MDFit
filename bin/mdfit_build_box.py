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

def main(master_dir, SCHRODINGER, args, charge, ligname, multisim_host, bmincomplex, template_dir):
    #Prepare Schrodinger multisim command ($SCHRODINGER/utilities/multisim)
    run_cmd = os.path.join(SCHRODINGER, "utilities", "multisim")

    #Generate output filename
    simbox="%s_md_setup_out.cms"%ligname

    #Generate setup filename
    inputfile="%s_md_setup.msj"%ligname

    #Generate ligand-specific job name
    jobname="%s_setup"%ligname

    #Check that simulation box does not exist
    if os.path.isfile(os.path.join(master_dir, "desmond_md", ligname, "md_setup", simbox)) == False:
        #If not, check system charge
        if charge > 0:
            #If positive, set template filename to positive
            filename = os.path.join(template_dir, "positive_template.msj")

        elif charge == 0:
            #If neutral, set template filename to netural
            filename = os.path.join(template_dir, "neutral_template.msj")
        
        #Must be negative
        else:
            #If negative, set template filename to negative
            filename = os.path.join(template_dir, "negative_template.msj")
        
        #Read in template file
        with open(filename, "r") as template:
            #Put lines in a variable
            lines = template.readlines()
        
        #Open setup filename for writing
        with open(inputfile, "w") as ligoutput:
            #Iterate through all the template lines
            
            for line in lines:
                #Write line to out file, replacing solvent keyword with desired solvent
                ligoutput.write(line.replace("<solvent>",args.solvent))
        
        #Generate command for building the box
        command = [run_cmd, "-maxjob", "1", "-JOBNAME", jobname, "-m", inputfile, bmincomplex, "-o", simbox, "-OPLSDIR", args.oplsdir, "-HOST", multisim_host, "-WAIT"]

        #Document current step
        logger.info("Building simulation box: %s"%simbox)

        #Run command
        run_job(command)

    #Simulation box exists
    else:
        #Document current step
        logger.info("Simulation box found: %s"%simbox)

    #Return output filename
    return simbox

if __name__ == '__main__':
    main(master_dir, SCHRODINGER, args, charge, ligname, multisim_host, bmincomplex, template_dir)