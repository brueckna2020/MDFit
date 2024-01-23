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
from schrodinger import structure

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

def filecheck(args, master_dir):
    #Document current step
    logger.info('Checking working directory for provided files: %s'%master_dir)

    #Check file existance, if provided by user
    #Generate list with all possible files
    filenames=[args.prot, args.liglib, args.precomplex]
    
    #Iterate over list of files
    for file in filenames:
        #Check if filename was provided by user
        if file != None:
            #If filename provided, check it exists
            exists = os.path.exists(file)
            
            #If it does not exist
            if exists == False:
                #Log error
                logger.critical("%s is not accessible or does not exist; "\
                "cannot proceed"%file)
                
                #Exit
                sys.exit()
    
    #Document current step
    logger.info("All provided filenames were successfully located")

def set_vars(args, master_dir, SCHRODINGER):
    #Get file extension for ligand library (e.g., ".sdf")
    if args.liglib and not args.precomplex:
        ligfiletype = os.path.splitext(args.liglib)[-1].lower()
    elif args.precomplex:
        ligfiletype = os.path.splitext(args.precomplex)[-1].lower()

    #Get filename, extension removed (e.g., "ligand_library")
    if args.liglib:
        ligfileprefix = os.path.splitext(args.liglib)[0]
    elif args.precomplex:
        ligfileprefix = os.path.splitext(args.precomplex)[0]

    #Get file extension for protein (e.g., ".mae")
    if args.prot:
        protfiletype = os.path.splitext(args.prot)[-1].lower()
    else:
        protfiletype = ".mae"

    #Check if ligand library extension is mae or sdf
    if ligfiletype != ".sdf" and ligfiletype != ".mae":
        #If not, log error
        logger.critical("%s must be in mae or sdf format; cannot proceed"%args.liglib)
    
        #Exit
        sys.exit(1)
    
    #Check if protein extension is mae
    if protfiletype != ".mae" and not args.precomplex:
        #If not, log error
        logger.critical("%s must be in mae format; cannot proceed"%args.prot)
    
        #Exit
        sys.exit(1)
    
    #Check if ligand library extension is mae and convert to SDF for downstream compatibility and non-Schrodinger MD engines
    if ligfiletype == ".mae" and not args.precomplex:
        #Set up Schrodinger run command ($SCHRODINGER/utilities/structconvert)
        run_cmd = os.path.join(SCHRODINGER, 'utilities', 'structconvert')

        #Prepare full command to convert mae file to sdf
        command = [run_cmd, args.liglib, "%s.sdf"%ligfileprefix]

        #Run the command using subprocess
        run_job(command)

        #Change filetype to sdf
        ligfiletype = ".sdf"

    #Return ligand library extension, ligand library name, and protein extension
    return ligfiletype, ligfileprefix, protfiletype

def count_ligs(args, ligfiletype, maxliglimit):
    #Initiate variable
    nlig = 0
    
    #Use StructureReader to iterate through ligands
    if args.liglib and not args.precomplex:
        for s in structure.StructureReader(args.liglib):
            #Increment nlig for each ligand
            nlig+=1
    elif args.precomplex:
        for s in structure.StructureReader(args.precomplex):
            #Increment nlig for each ligand
            nlig+=1

    #If ligands are not found
    if nlig == 0:
        #Log error
        logger.critical("No ligands captured. Please check input file.")

        #Exit
        sys.exit(1)
    
    #Ligands must have been found
    else:
        #Document current step
        logger.info("Number of ligands in library = %s"%nlig)

        #Check that the number of ligands is less than the max limit for MD
        if nlig > maxliglimit and args.skip_md == False:
            #If true, log error
            logger.critical("Number of ligands in library (%s) exceeds the "\
            "allowed limit (%s); cannot proceed" % (nlig, maxliglimit))

            #Exit
            sys.exit(1)

    #Return number of ligands
    return nlig

def main(args, master_dir, maxliglimit, SCHRODINGER):
    #Check if files exist and dependencies are met
    filecheck(args, master_dir)

    #Check file extensions
    ligfiletype, ligfileprefix, protfiletype = set_vars(args, master_dir, SCHRODINGER)
    
    #Count number of ligands in ligand library
    nlig = count_ligs(args, ligfiletype, maxliglimit)

    #Return ligand library extension, ligand library name, protein extension, and number of ligands
    return ligfiletype, ligfileprefix, protfiletype, nlig

if __name__ == '__main__':
    main(args, master_dir, maxliglimit, SCHRODINGER)
