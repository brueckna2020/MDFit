#!/ap/rhel7/bin/python3.6

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import os
import shutil
import subprocess
import re

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

def main(SCHRODINGER, ligname, master_dir, args):
    #Prepare Schrodinger proplister command ($SCHRODINGER/utilities/proplister)
    run_cmd = os.path.join(SCHRODINGER, "utilities", "proplister")

    #Check if proplister has been run before
    if os.path.isfile(os.path.join(master_dir, "desmond_md", ligname, "md_setup", "%s_atoms.csv"%ligname)) == False:
        #If not, prepare proplister command
        command = [run_cmd, "-atom_bond_props", "%s_out_complex_min.mae"%ligname, "-c", "-o", "%s.csv"%ligname]

        #Run proplister
        run_job(command)

    #Proplister has been run before
    else:
        #Copy proplister output from md_setup directory to scratch space
        shutil.copy(os.path.join(master_dir, "desmond_md", ligname, "md_setup", "%s_atoms.csv"%ligname), "%s_atoms.csv"%ligname)

    #Define pattern for matching
    fcFinder = re.compile(r'i_m_formal_charge')

    #Initiate variable for counting lines
    lineCount = 0

    #Initiate total charge variable
    totQ = 0

    #Read in proplister output
    with open("%s_atoms.csv"%ligname, "r") as inFile:
        #Initiate infinite loop to iterate through file
        while 1:
            #Read in next line of file
            dataLine = inFile.readline()

            #Break loop if end of file
            if not dataLine: break

            #Split line into list by comma (csv)
            tmpList = dataLine[:-1].split(",")

            #Check if first line
            if lineCount == 0:
                #Initiate variable for number of columns
                columnCount = 0

                #Iterate over all columns in first line of file
                for column in tmpList:
                    #Locate the formal charge column
                    theMatch =  fcFinder.match(column)

                    #If formal charge column is located
                    if theMatch:
                        #Get column number
                        chargeColumn = columnCount

                        #Break loop
                        break
                    
                    #Increment column variable 
                    columnCount += 1
            
            #Not first line
            else:
                #Increment by value in formal charge column
                totQ += int(tmpList[chargeColumn])

            #Increment line count variable
            lineCount += 1
    
    #Document current step
    logger.info("Total system charge for %s: %s"%(ligname, totQ))

    #Return total system charge
    return totQ

if __name__ == '__main__':
    main(SCHRODINGER, ligname. master_dir, args)