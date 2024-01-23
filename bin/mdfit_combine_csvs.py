#!/ap/rhel7/bin/python3.6

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import os
import pandas as pd
import glob

###Initiate logger###
logger = logging.getLogger(__name__)

def generate_master_simfp(master_dir, df_simfp):
    #Initiate empty list in case files do not exist
    simfp_scratch_files = []
    simfp_files = []
    
    #Get paths to individual SimFP files in scratch directory
    simfp_scratch_files = glob.glob(os.path.join(master_dir, "desmond_md_analysis", "scratch", "*SimFP.csv"))

    #Get paths to individual SimFP files in permanent directories
    simfp_files = glob.glob(os.path.join(master_dir, "desmond_md_analysis", "*", "*repetition*", "*SimFP.csv"))
    
    #Iterate over files in the scratch directory
    for file in simfp_scratch_files:
        #Add to list of files in permanent directories
        simfp_files.append(file)

    #Iterate over each file
    for file in simfp_files:
        #Read file into temporary dataframe
        df_temp = pd.read_csv(file)
        
        #Append ligand SimFP to master SimFP dataframe
        df_simfp = df_simfp.append(df_temp, ignore_index=True)
    
    #Sort master SimFP dataframe by molecule name and replace "NaN" values with zeros
    df_simfp = df_simfp.sort_values(by=['Molecule', 'Repetition']).fillna("0.0000")

    #Remove duplicate ligand entires (if user re-runs analysis)
    no_duplicates = df_simfp.drop_duplicates()

    #Return master SimFP dataframe
    return no_duplicates

def generate_master_compat(master_dir, df_compat):
    #Initiate empty list in case files do not exist
    compat_scratch_files = []
    compat_files = []

    #Get paths to individual compatibility files in scratch directory
    compat_scratch_files = glob.glob(os.path.join(master_dir, "desmond_md_analysis", "scratch", "*compatibility.csv"))

    #Get paths to individual compatibility files in permanent directories
    compat_files = glob.glob(os.path.join(master_dir, "desmond_md_analysis", "*", "*repetition*", "*compatibility.csv"))

    #Iterate over files in the scratch directory
    for file in compat_scratch_files:
        #Add to list of files in permanent directories
        compat_files.append(file)

    #Iterate over each file
    for file in compat_files:
        #Read file into temporary dataframe
        df_temp = pd.read_csv(file)

        #Append ligand compatibility to master compatibility dataframe
        df_compat = df_compat.append(df_temp, ignore_index=True)

    #Sort master compatibility dataframe by molecule name and replace "NaN" values with zeros
    df_compat = df_compat.sort_values(by=['Molecule', 'Repetition']).fillna("0.0000")

    #Remove duplicate ligand entires (if user re-runs analysis)
    no_duplicates = df_compat.drop_duplicates()

    #Return master compatibility dataframe
    return no_duplicates

def main(master_dir):
    #Initiate master SimFP dataframe
    df_simfp = pd.DataFrame()

    #Initiate master compatibility dataframe
    df_compat = pd.DataFrame()

    #Generate final SimFP dataframe
    df_simfp_final = generate_master_simfp(master_dir, df_simfp)

    #Generate final compatibility dataframe
    df_compat_final = generate_master_compat(master_dir, df_compat)

    #Write final SimFP dataframe to "MDFit_SimFPs.csv" file in desmond_md_analysis
    df_simfp_final.to_csv(os.path.join(master_dir, "desmond_md_analysis", "MDFit_SimFPs.csv"), index=False)

    #Write final compatibility dataframe to "MDFit_Compatibility.csv" file in desmond_md_analysis
    df_compat_final.to_csv(os.path.join(master_dir, "desmond_md_analysis", "MDFit_Compatibility.csv"), index=False)

    #Document current step
    logger.info("SimFPs are captured in %s"%os.path.join(master_dir, "desmond_md_analysis", "MDFit_SimFPs.csv"))

    #Document current step
    logger.info("Compatibility metrics are captured in %s"%os.path.join(master_dir, "desmond_md_analysis", "MDFit_Compatibility.csv"))

if __name__ == '__main__':
    main(master_dir)