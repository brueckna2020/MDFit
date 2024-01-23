#!/ap/rhel7/bin/python

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import sys
import os

#Get MDFit installation path
MDFit_path = os.path.dirname(__file__)

#Add MDFit bin directory to path
sys.path.insert(0, os.path.join(MDFit_path, 'bin'))

#Import MDFit modules
import mdfit_read_params
import mdfit_parseargs
import mdfit_initiate
import mdfit_ffbuilder
import mdfit_desmond_md
import mdfit_desmond_analysis

#Generate path to template directory
template_dir = os.path.join(MDFit_path, 'templates')

#Get path to user directory
master_dir = os.getcwd()

#Get Schrodinger environmental variable
SCHRODINGER = os.getenv('SCHRODINGER')

#Get Schrodinger release version. Assumes pathname has version
#E.g., "/schrodinger/2023-2/"
schrodinger_version = os.path.basename(SCHRODINGER)

#Get home path environmental variable
homepath = os.getenv('HOME')

#Initiate logger
logger = logging.getLogger()

#Point logger to file
fh = logging.FileHandler(os.path.join(master_dir, 'MDFit.log'))

#Create writing format for logging
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

#Add to logger
logger.addHandler(fh)

#Set logger default to debug
logger.setLevel(logging.DEBUG)

def read_json(MDFit_path):
    #Read in instiutional parameters ("inst params")
    #Hostnames, maximum number of ligands, number of processors for FFBuilder
    #Calls mdfit_read_params.py
    inst_params = mdfit_read_params.main(MDFit_path)

    #Return parameters
    return inst_params

def parseargs(master_dir, homepath):
    #Get user flags and options
    #Calls mdfit_parseargs.py
    args = mdfit_parseargs.main(master_dir, homepath)

    #Set logger level based on user input
    logger.setLevel(args.loglevel)

    #Print arguments for future reference
    logger.info('Parsed arguments: %s', args)

    #Return arguments
    return args

def initiate_mdfit(SCHRODINGER, args, master_dir, maxliglimit):
    #Document current step
    logger.info("Initiating MDFit...")
    
    #Calls mdfit_initiate.py
    ligfiletype, ligfileprefix, protfiletype, nlig = mdfit_initiate.main(args, \
        master_dir, maxliglimit, SCHRODINGER)
    
    #Document current step
    logger.info("Completed initiation of MDFit")

    #Return arguments
    return ligfiletype, ligfileprefix, protfiletype, nlig

def run_ffbuilder(args, master_dir, SCHRODINGER, ligpath, ligfileprefix, schrodinger_version, inst_params, homepath):
    #Check if user wants FFBuilder
    if args.skip_ff == False:
        #If they do, document current step
        logger.info("Initiating FFBuilder...")

        #Calls mdfit_ffbuilder.py
        mdfit_ffbuilder.main(args, master_dir, SCHRODINGER, ligpath, \
            ligfileprefix, schrodinger_version, inst_params, homepath)

        #Document current step
        logger.info("Completed FFBuilder")
    
    #User requests to skip FFBuilder
    else:
        #Document current step
        logger.info("Skipping FFBuilder")

    #Useful to check that ligand file is correctly assigned
    logger.debug("Current ligand file = %s"%ligpath)

def run_md(args, master_dir, ligfileprefix, SCHRODINGER, ligpath, template_dir, inst_params):
    #Check if user wants Desmond MD
    if args.skip_md == False:
        #If they do, document current step
        logger.info("Initiating Desmond MD...")

        #Calls mdfit_desmond_md.py
        mdfit_desmond_md.main(args, master_dir, ligfileprefix, SCHRODINGER, ligpath, template_dir, inst_params)
        
        #Document current step
        logger.info("Completed Desmond MD")

    #User requests to skip Desmond MD
    else:
        #Document current step
        logger.info("Skipping Desmond MD")

def run_analysis(args, master_dir, SCHRODINGER, inst_params):
    #Check if user wants Desmond MD analysis
    if args.skip_analysis == False:
        #If they do, document current step
        logger.info("Initiating MD analysis...")

        #Calls mdfit_desmond_analysis.py
        mdfit_desmond_analysis.main(args, master_dir, SCHRODINGER, inst_params)
        
        #Document current step
        logger.info("Completed MD analysis")
    
    #User requests to skip Desmond MD analysis
    else:
        #Document current step
        logger.info("Skipping MD analysis")

def main():
    #Get institution parameters from json file (hostnames, max number of ligs, etc.)
    inst_params = read_json(MDFit_path)
    
    #Get user flags and options
    args = parseargs(master_dir, homepath)
    
    #Get maximum number of ligands from json file
    maxliglimit = inst_params["parameters"]["MAXLIGS"]
    
    #Check file viability, flag compatibility, etc.
    ligfiletype, ligfileprefix, protfiletype, nlig = initiate_mdfit(SCHRODINGER, args, master_dir, maxliglimit)

    #Generate path to ligand library
    if args.liglib and not args.precomplex:
        ligpath = os.path.join(master_dir, "%s.sdf"%ligfileprefix)
    elif args.precomplex:
        ligpath = os.path.join(master_dir, args.precomplex)

    #Run FFBuilder, if requested
    run_ffbuilder(args, master_dir, SCHRODINGER, ligpath, \
        ligfileprefix, schrodinger_version, inst_params, homepath)
    
    #Run Desmond MD, if requested
    run_md(args, master_dir, ligfileprefix, SCHRODINGER, ligpath, template_dir, inst_params)

    #Analyze Desmond trajectories, if requested
    run_analysis(args, master_dir, SCHRODINGER, inst_params)

if __name__ == '__main__':
    main()