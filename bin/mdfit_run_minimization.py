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

def main(ligname, pvcomplex, args, bmin_host, SCHRODINGER, master_dir, template_dir):
    #Generate output minimized complex filename
    bmincomplex = "%s_out_complex_min.mae"%ligname

    #Check if minimized complex exists
    if os.path.isfile(os.path.join(master_dir, "desmond_md", ligname, "md_setup", bmincomplex)) == False:
        #If not, read in minimization template
        with open(os.path.join(template_dir, "bmin_template.com"), "r") as template:
            #Put all lines in variable
            lines = template.readlines()
        
        #Open ligand-specific job file for writing
        with open("%s_min.com"%ligname, "w") as ligoutput:
            #Iterate over all lines in template
            for line in lines:
                #Write line to file, replacing key strings IN_NAME and OUT_NAME (complex filename and output filename)
                ligoutput.write(line.replace("IN_NAME","%s_out_complex.mae"%ligname).replace("OUT_NAME","%s_out_complex_min.mae"%ligname))
        
        #Prepare Schrodinger's bmin command ($SCHRODINGER/bmin)
        run_cmd = os.path.join(SCHRODINGER, "bmin")

        #Prepare minimization command
        command = [run_cmd, "%s_min"%ligname, "-OPLSDIR", args.oplsdir, "-HOST", bmin_host, "-WAIT"]

        #Capture current step
        logger.info("Running minimization: %s"%' '.join(command))

        #Run minimization
        run_job(command)
    
    #Minimized complex exists
    else:
        #Capture current step
        logger.info("Minimized complex found: %s"%bmincomplex)
    
    #Return minimized complex filename
    return bmincomplex

if __name__ == '__main__':
    main(ligname, pvcomplex, args, bmin_host, SCHRODINGER, master_dir, template_dir)