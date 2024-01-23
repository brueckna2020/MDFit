#!/ap/rhel7/bin/python3.6

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import sys
import os
import pandas as pd

#Import MDFit modules
import mdfit_slicetrj

###Initiate logger###
logger = logging.getLogger(__name__)

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

def simfp(dat_files, round_int, basename, master_dir, num_frames, args, compat_prep, ligbase, repnum):
    #Initiate SimFP dataframe with ligand and repetition information
    simfp_prep = pd.DataFrame({'Molecule':['Repetition'], ligbase:[repnum]})

    #Iterate over all dat files
    for file in os.listdir(dat_files):
        #Pick out protein-ligand interaction files
        if file.startswith('PL-Contacts') and file.endswith('.dat'):
            #Get interaction type based on filename
            int_type = file.split('_')[1].split('.dat')[0]
            
            #Initiate dataframe for the dat file
            df = pd.read_csv(os.path.join(dat_files, file), sep="\s+")

            #Drop first column (extra "#")
            df = df.shift(axis=1).drop('#', axis=1)

            #If reading metal interaction dat file
            if file.endswith('Metal.dat'):
                #Remove protein-metal interactions
                df = df[df["Type"].str.contains("prot") == False]

                #Calculate average number of interactions per frame
                avg_int = round((len(df.index)/num_frames), round_int)

                #Add average number of metal interactions to compatibility dataframe
                compat_prep.loc[len(compat_prep.index)] = ["Average_%s_per_frame"%int_type, avg_int]

                #Generate SimFP notation (Chain:ResNum:InteractionType) modified for metals (no chain)
                df['Sort'] = '_:' + df['MetalSite'] + ':%s'%int_type
                
                #Initiate temporary dataframe with unique SimFPs
                add_res = pd.DataFrame(df['Type'].groupby(df['Sort']).count().index.values, columns=['Molecule'])

                #Calculate SimFPs (fraction of time interaction occurs across frames)
                add_res[ligbase] = df['Type'].groupby(df['Sort']).count().values/num_frames

                #Round to desired decimal places
                add_res[ligbase] = add_res[ligbase].round(round_int)

                #Remove SimFPs below cutoff
                add_res[add_res[ligbase]>=args.analysis_cutoff]
                
                #Combine interaction-specific dataframe into full dataframe
                simfp_prep = simfp_prep.append(add_res,ignore_index=True)

            #Not metal interaction dat file
            else:
                #Calcaulte average number of interactions per frame
                avg_int = round((len(df.index)/num_frames), round_int)

                #Add average number of metal interactions to compatibility dataframe
                compat_prep.loc[len(compat_prep.index)] = ["Average_%s_per_frame"%int_type, avg_int]

                #Generate SimFP notation (Chain:ResNum:InterationType)
                df['Sort'] = df['Chain'] + ':' + df['Residue#'].astype(str) + ':%s'%int_type

                #Initiate temporary dataframe with unique SimFPs
                add_res = pd.DataFrame(df['Residue#'].groupby(df['Sort']).count().index.values, columns=['Molecule'])

                #Calculate SimFPs (fraction of time interaction occurs across frames)
                add_res[ligbase] = df['Residue#'].groupby(df['Sort']).count().values/num_frames
                
                #Round to desired decimal places
                add_res[ligbase] = add_res[ligbase].round(round_int)

                #Remove SimFPs below cutoff
                add_res[add_res[ligbase]>=args.analysis_cutoff]
            
                #Combine interaction-specific dataframe into full dataframe
                simfp_prep = simfp_prep.append(add_res,ignore_index=True)

    #Transpose SimFP dataframe and write to csv file
    simfp_prep.transpose().to_csv(os.path.join(master_dir, "desmond_md_analysis", "scratch", "%s_SimFP.csv"%basename), header=False)

def compatibility(dat_files, round_int, basename, master_dir, num_frames, args, compat_prep):
    #Iterate over all dat files
    for file in os.listdir(dat_files):
        #If reading ligand properties dat file
        if file == "L-Properties.dat":
            #Initiate dataframe for the dat file
            df = pd.read_csv(os.path.join(dat_files, file), sep="\s+")

            #Drop first column to fix spacing issue
            df = df.shift(axis=1).drop('Frame', axis=1)

            #Rename "#" to "Frame"
            df = df.rename(columns={'#': 'Frame'})

            #Iterate over all frames in dataframe
            for col in df.columns:
                #Check if not reading frame column
                if "Frame" not in col:
                    #Calculate the average value for the given property
                    avg_val = df.loc[:, '%s'%col].mean().round(round_int)

                    #Add average to compatibility dataframe
                    compat_prep.loc[len(compat_prep.index)] = ["Avg_lig_%s"%col, avg_val]

        #Check if reading ligand RMSF dat file
        elif file == "L_RMSF.dat":
            #Initiate dataframe for the dat file
            df = pd.read_csv(os.path.join(dat_files, file), delim_whitespace=True, na_values=[''])

            #Drop first column to fix spacing (stray "#")
            df = df.shift(axis=1).drop('#', axis=1)

            #"PDBResName" can be empty. Hack to get around alignment issues in pandas
            #Check if last column in dataframe is empty (NaN)
            if df['wrt_Ligand'].isnull().values.any():
                #If it is, shift the dataframe over and drop the Atom# column
                df = df.shift(axis=1).drop('Atom#', axis=1)

                #Rename PDBResName to Frame
                df = df.rename(columns={'PDBResName': 'Frame'})

            #Iterate over all columns in dataframe
            for col in df.columns:
                #Check if reading property column
                if "wrt" in col:
                    #Calculate the average value for the given property
                    avg_val = df.loc[:, '%s'%col].mean().round(round_int)

                    #Add average to compatibility dataframe
                    compat_prep.loc[len(compat_prep.index)] = ["Avg_ligRMSF_%s"%col, avg_val]

        #Check if reading protein and ligand RMSD dat file
        elif file == "PL_RMSD.dat":
            #Initiate dataframe for the dat file
            df = pd.read_csv(os.path.join(dat_files, file), sep="\s+")

            #Drop first column to fix spacing issue (stray "#")
            df = df.shift(axis=1).drop('#', axis=1)

            #Iterate over all columns in dataframe
            for col in df.columns:
                #Check if column is not "frame"
                if "frame" not in col:
                    #Calculate average value for the given property
                    avg_val = df.loc[:, '%s'%col].mean().round(round_int)

                    #Add average to compatibility dataframe
                    compat_prep.loc[len(compat_prep.index)] = ["Avg_PL_RMSD_%s"%col, avg_val]

        #Check if reading protein RMSF dat file
        elif file == "P_RMSF.dat":
            #Initiate dataframe for the dat file
            df = pd.read_csv(os.path.join(dat_files, file), sep="\s+")

            #Drop first column to fix spacing (stray "#")
            df = df.shift(axis=1).drop('#', axis=1)

            #Initiate list with columns of interest
            columns = ["CA", "Backbone", "Sidechain", "All_Heavy"]

            #Iterate over list of column names
            for col in columns:
                #Calculate average value for the given property
                avg_val = df.loc[:, '%s'%col].mean().round(round_int)

                #Add average to compatibility dataframe
                compat_prep.loc[len(compat_prep.index)] = ["Avg_protRMSF_%s"%col, avg_val]
        
    #Transpose compatibility dataframe and write to csv file
    compat_prep.transpose().to_csv(os.path.join(master_dir, "desmond_md_analysis", "scratch", "%s_compatibility.csv"%basename), header=False)

def main(SCHRODINGER, rep, master_dir, args):
    #Generate repetition name <ligname>-repetition<#>
    basename = os.path.basename(rep)

    #Generate ligand name <ligname>
    ligbase = basename.split("_repetition")[0]

    #Get repetition number
    repnum = basename.split("_repetition")[-1]

    #Check if dat files are in scratch
    if os.path.isfile(os.path.join(master_dir, "desmond_md_analysis", "scratch", basename, "P_RMSF.dat")) == True:
        #If they are, set path to scratch space
        dat_files = os.path.join(master_dir, "desmond_md_analysis", "scratch", basename)
    
    #Check if dat files are in permanent space
    elif os.path.isfile(os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, basename, "P_RMSF.dat")) == True:
        #If they are, set path to permanent space
        dat_files = os.path.join(master_dir, "desmond_md_analysis", ligbase, basename, basename)
    
    #Cannot fine dat files
    else:
        #Capture error
        logger.critical("Dat files could not be located for %s. Try removing desmond_md_analysis directory are re-running analysis."%basename)

        #Exit
        sys.exit()

    #Generate path to MD trajectories
    md_path = os.path.join(master_dir, "desmond_md", ligbase, basename)

    #Generate paths to trajectory files
    cms_path, trj_path = trj_pathnames(md_path, basename)

    #Initiate compatibility dataframe with ligand and repetition info
    compat_prep = pd.DataFrame({'Molecule':['Repetition'], ligbase:[repnum]})

    #Get number of frames. Calls mdfit_slicetrj.py
    num_frames = mdfit_slicetrj.count_frames(trj_path)

    #Number of decimal places for rounding
    round_int=4

    #Generate repetition-specific SimFPs
    simfp(dat_files, round_int, basename, master_dir, num_frames, args, compat_prep, ligbase, repnum)

    #Generate repetition-specific compatibility metrics
    compatibility(dat_files, round_int, basename, master_dir, num_frames, args, compat_prep)

if __name__ == '__main__':
    main(SCHRODINGER, rep, master_dir, args)