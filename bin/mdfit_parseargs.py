#!/ap/rhel7/bin/python

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import textwrap
import argparse
import sys
import os

###Initiate logger###
logger = logging.getLogger(__name__)

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        logger.critical(message)
        print("An error has occurred. Check log file for information.")
        run_command(('kill','0'))

    """Disables prefix matching in ArgumentParser."""
    def _get_option_tuples(self, option_string):
        """Prevent argument parsing from looking for prefix matches."""
        return []

def parse_arguments(master_dir, homepath):
    parser = ArgumentParser(prog='MDFit', formatter_class=argparse.RawDescriptionHelpFormatter, usage='%(prog)s [options]',
                                     description=textwrap.dedent('''\
        ----------------------------------------------
        MDFit workflow:
            a) Run FFBuilder to optimize ligand parameters
            b) Prepare protein-ligand complexes using user-supplied protein mae file
            c) Solvate each protein-ligand complex
            d) Run Desmond MD with each of the solvated systems
            e) Generate SimFPs and compatibility information
            f) Cluster the simulation, reporting representative structures
         '''))

    structure = parser.add_argument_group("STRUCTURE INPUT")
    ffbuilder = parser.add_argument_group("FFBUILDER")
    desmond = parser.add_argument_group("DESMOND MD")
    analysis = parser.add_argument_group("MD ANALYSIS")
    clustering = parser.add_argument_group("MD CLUSTERING")
    misc = parser.add_argument_group("MISCELLANEOUS")

    structure.add_argument('-p', '--prot', dest='prot',  default=None, help='protein mae file; must also provide liglib')
    structure.add_argument('-l', '--liglib', dest='liglib',  default=None, help='ligand library in mae or sdf format; must also provide prot')
    structure.add_argument('--precomplex', dest='precomplex', default=None, help='mae file with protein and ligand already complexed (e.g., crystal structure); skips FFBuilder')

    ffbuilder.add_argument('--skip_ff', dest='skip_ff', action='store_true', help='skip FFBuilder; default = false')
    ffbuilder.add_argument('-o', '--oplsdir', dest='oplsdir', default='%s/.schrodinger/opls_dir'%homepath, help='path to custom forcefield; default = %s/.schrodinger/opls_dir'%homepath)

    desmond.add_argument('--skip_md', dest='skip_md', action='store_true', help='skip MD simulation; default = false')
    desmond.add_argument('--solvent', dest='solvent',  default='SPC', help='SPC/TIP3P; default = SPC')
    desmond.add_argument('-t', '--md_sim_time', dest='md_sim_time', type=float, default='2000', help='in picoseconds; default = 2000')
    desmond.add_argument('--md_traj_write_freq', dest='md_traj_write_freq', type=float, default='100', help='in picoseconds; default = 100')
    desmond.add_argument('-r', '--md_repetitions', dest='md_repetitions', type=int, default='1', help='number of MD simulations to run for each ligand, each with a different random seed; default = 1')

    analysis.add_argument('--skip_analysis', dest='skip_analysis', action='store_true', help='skip MD simulation analysis; default = false')
    analysis.add_argument('--slice_start', dest='slice_start', type=int, default=0, help='frame to start analysis. default: 0')
    analysis.add_argument('--slice_end', dest='slice_end', help='frame to end analysis. default: last frame')
    analysis.add_argument('--analysis_lig', dest='analysis_lig', default='all', help='name of ligand for MD analysis; default = all')
    analysis.add_argument('--prot_ASL', dest='prot_ASL', default='"protein"', help='ASL definition for protein; default = "protein"')
    analysis.add_argument('--lig_ASL', dest='lig_ASL', default='"auto"', help='ASL definition for ligands; default = "auto"')
    analysis.add_argument('--analysis_cutoff', dest='analysis_cutoff', type=float, default='0.0000', help='interactions above this percentage of the simulation will be recorded; default=0.0000')
    
    clustering.add_argument('--skip_cluster', dest='skip_cluster', action='store_true', help='skip trajectory clustering; default = false')
    clustering.add_argument('--n_clusters', dest='n_clusters', type=int, default='5', help='number of clusters to output; default = 5')
    clustering.add_argument('--rmsd_ASL', dest='rmsd_ASL', default='"auto"', help='ASL definition for RMSD clustering (e.g., ligand); default = "auto"')
    clustering.add_argument('--centering_ASL', dest='centering_ASL', default='"protein"', help='ASL definition for centering the trajectory (e.g., binding site residues); default = protein')
    clustering.add_argument('--parch_align_ASL', dest='parch_align_ASL', default='"protein"', help='ASL definition for alignment during parching (e.g., binding site residues); default = protein')
    clustering.add_argument('--parch_solv_ASL', dest='parch_solv_ASL', default='"auto"', help='ASL definition for atoms around which solvent is retained; default = "auto"')
    clustering.add_argument('--n_solv', dest='n_solv', type=int, default='100', help='number of solvent molecules to keep during parching; default = 100')

    misc.add_argument('-m', '--max_workers', dest='max_workers', type=int, default=0, help='number of workers for multitasking; default = min(32, os.cpu_count() + 4)')
    misc.add_argument('-d', '--debug', action='store_const', dest='loglevel', const=logging.DEBUG, default=logging.INFO, help='Print all debugging statements to log file')

    #Get all arguments and check for any unknown variables
    args,unknowns = parser.parse_known_args()

    #Check if no options passed to script
    if len(sys.argv)==1:
        #Capture error
        logger.critical("provide '-prot' and '-liglib' for basic functionality")

        #Print help statement
        parser.print_help()

        #Exit
        sys.exit()

    #Check if unknown variables passed to script
    if unknowns:
        #Document warning and ignore variables
        logger.warning('ignoring unrecognized arguments: %s'%unknowns)

    #Check if protein and ligands are pre-complexed
    if not args.precomplex:
        #If not, check if protein and ligand library files are provided
        if not args.prot or not args.liglib:
            #If not, capture error
            logger.critical("'-prot' and '-liglib' arguments are dependent on each other. Alternatively, provide '-precomplex'")

            #Exit
            sys.exit()

    #Protein and ligands are pre-complexed
    else:
        #Get filetype
        complexfiletype = os.path.splitext(args.precomplex)[-1].lower()

        #Check it is mae
        if complexfiletype == ".mae":
            #Skip FFBuilder
            args.skip_ff=True

            #Remove protein filename
            args.prot=None

            #Remove ligand filename
            args.liglib=None
        
        #Filetype is not mae
        else:
            #Capture error
            logger.critical("Precomplexed systems must be in MAE format")

            #Exit
            sys.exit()

    #Return all arguments
    return args

def main(master_dir, homepath):
    #Get arguments from user or script defaults
    args = parse_arguments(master_dir, homepath)

    #Return all arguemnts
    return args

if __name__ == '__main__':
    main(master_dir, homepath)
