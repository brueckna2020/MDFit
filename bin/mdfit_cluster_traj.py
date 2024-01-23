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
import glob

#Import Schrodinger modules
from schrodinger import structure
from schrodinger.structutils import analyze

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

def center_traj(SCHRODINGER, cms_path, trj_path, run_cmd, basename, args):
    #Prepare centering command
    command = [run_cmd, "trj_center.py", "-t", trj_path, "-asl", args.centering_ASL, cms_path, "%s_centered"%basename]

    #Capture current step
    logger.info("Centering trajectory: %s"%' '.join(command))

    #Run centering command
    run_job(command)

def lig_identifier(args, ref_path):
    #Read in reference structure
    struct = structure.StructureReader.read(ref_path)

    #Initiate Schrodinger's ligand searcher utility
    ligand_searcher = analyze.AslLigandSearcher()

    #Set minimum atom count
    ligand_searcher.min_atom_count = 15

    #Set maximum atom count
    ligand_searcher.max_atom_count = 300

    #Excluse ions as ligands
    ligand_searcher.exclude_ions = True

    #Include amino acids (peptides)
    ligand_searcher.exclude_amino_acids = False

    #Search reference structure given search criteria
    ligand_list = ligand_searcher.search(struct)

    #Grab most-likely ligand from all possible ligands
    ligand = max(ligand_list, key=lambda lig: len(lig.atom_indexes))

    #Return ligand ASL
    return ligand

def parch_traj(SCHRODINGER, ligbase, basename, args, run_cmd, center_cms, center_trj, master_dir, ref_path):
    #Check if parch ASL is set to default
    if args.parch_solv_ASL == '"auto"':
        #If it is, identify ligand ASL using Schrodinger's utilities
        ligand = lig_identifier(args, ref_path)

        #Set argument to identified ligand ASL
        args.parch_solv_ASL = "%s"%ligand.ligand_asl

    #Prepare trajectory parching command
    command = [run_cmd, "trj_parch.py", "-output-trajectory-format", "auto", "-ref-mae", ref_path, "-align-asl", args.parch_align_ASL, "-dew-asl", '"%s"'%args.parch_solv_ASL, "-n", str(args.n_solv), center_cms, center_trj, "%s_parched"%basename]
    
    #Capture current step
    logger.info("Parching trajectory: %s"%' '.join(command))

    #Run parching command
    run_job(command)

def cluster_traj(SCHRODINGER, basename, args, run_cmd, ref_path, parch_cms, parch_trj):
    #Check if rmsd ASL is set to default
    if args.rmsd_ASL == '"auto"':
        #If it is, identify ligand ASL using Schrodinger's utilities
        ligand = lig_identifier(args, ref_path)

        #Set argument to identified ligand ASL
        args.rmsd_ASL = "%s"%ligand.ligand_asl

    #Prepare trajectory clustering command
    command = [run_cmd, "trj_cluster.py", parch_cms, parch_trj, "%s_cluster"%basename, "-rmsd-asl", '"%s"'%args.rmsd_ASL, "-n", str(args.n_clusters)]
    
    #Capture current step
    logger.info("Clustering trajectory: %s"%' '.join(command))

    #Run clustering command
    run_job(command)

def main(SCHRODINGER, rep, master_dir, args):
    #Prepare Schrodinger run command ($SCHRODINGER/run)
    run_cmd = os.path.join(SCHRODINGER, 'run')

    #Generate basename <ligand>-repetition<#>
    basename = os.path.basename(rep)

    #Get ligand basename <ligand>
    ligbase = basename.split("_repetition")[0]

    #Generate path to MD repetition dir
    md_path = os.path.join(master_dir, "desmond_md", ligbase, basename)

    #Generate path to reference (pre-simulation) file
    ref_path = "%s_out_complex_min.mae"%os.path.join(master_dir, "desmond_md", ligbase, "md_setup", ligbase)

    #Check if slice trajectory exists
    if os.path.isfile(os.path.join(md_path, "%s_sliced-out.cms"%basename)) == True:
        #If it does, set cms path to slice file
        cms_path = os.path.join(md_path, "%s_sliced-out.cms"%basename)

        #If it does, set trj path to slice trajectory
        trj_path = os.path.join(md_path, "%s_sliced_trj"%basename)
    #Check if unsliced trajectory does and sliced trajectory does not exist
    elif os.path.isfile(os.path.join(md_path, "%s_sliced-out.cms"%basename)) == False and os.path.isfile(os.path.join(md_path, "%s-out.cms"%basename)) == True:
        #If it does, set cms path to unsliced trajectory
        cms_path = os.path.join(md_path, "%s-out.cms"%basename)

        #If it does, set trj path to unsliced trajectory
        trj_path = os.path.join(md_path, "%s_trj"%basename)
    
    #Could not find trajectory
    else:
        #Log error
        logger.critical("Trajectory could not be located!")

        #Exit
        sys.exit()

    #Check if centered trajectory exists
    if os.path.isfile(os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, "%s_centered-out.cms"%basename)) == False:
        #Center trajectory
        center_traj(SCHRODINGER, cms_path, trj_path, run_cmd, basename, args)

        #Generate path to centered trajectory file
        center_cms = os.path.join(master_dir, "desmond_md_analysis", "scratch", "%s_centered-out.cms"%basename)

        #Generate path to centered trajectory directory
        center_trj = os.path.join(master_dir, "desmond_md_analysis", "scratch", "%s_centered_trj"%basename)
    
    #Centered trajectory exists
    else:
        #Generate path to centered trajectory file
        center_cms = os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, "%s_centered-out.cms"%basename)

        #Generate path to centered trajectory directory
        center_trj = os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, "%s_centered_trj"%basename)
        
        #Document current step
        logger.info("Centered trajectory found: %s"%center_cms)

    #Check if parched trajectory exists
    if os.path.isfile(os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, "%s_parched-out.cms"%basename)) == False:
        #Parch trajectory (remove excess waters)
        parch_traj(SCHRODINGER, ligbase, basename, args, run_cmd, center_cms, center_trj, master_dir, ref_path)

        #Generate path to parched trajectory file
        parch_cms = os.path.join(master_dir, "desmond_md_analysis", "scratch", "%s_parched-out.cms"%basename)

        #Generate path to parched trajectory directory
        parch_trj = os.path.join(master_dir, "desmond_md_analysis", "scratch", "%s_parched_trj"%basename)
    
    #Parched trajectory does not exist
    else:
        #Generate path to parched trajectory file
        parch_cms = os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, "%s_parched-out.cms"%basename)

        #Generate path to parched trajectory directory
        parch_trj = os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, "%s_parched_trj"%basename)
        
        #Document current step
        logger.info("Parched trajectory found: %s"%parch_cms)
    
    #Generate list of cluster files
    cluster_files = glob.glob(os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, "%s_cluster_0*.cms"%basename))

    #Check if cluster files exist
    if cluster_files == []:
        #Cluster trajectory
        cluster_traj(SCHRODINGER, basename, args, run_cmd, ref_path, parch_cms, parch_trj)
    
    #Cluster files exist
    else:
        logger.info("Cluster files found for %s. Skipping clustering."%basename)

if __name__ == '__main__':
    main(SCHRODINGER, rep, master_dir, args)