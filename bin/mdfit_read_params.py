#!/ap/rhel7/bin/python3.6

####################################################################
# Corresponding Authors : Alexander Brueckner, Kaushik Lakkaraju ###
# Contact : alexander.brueckner@bms.com, kaushik.lakkaraju@bms.com #
####################################################################

#Import Python modules
import logging
import sys
import os
import json

###Initiate logger###
logger = logging.getLogger(__name__)

def read_json(MDFit_path):
    #Open institution-based parameters json file for reading
    with open(os.path.join(MDFit_path, "parameters.json"), "r") as injson:
        #Put parameters in a list
        parameters = json.load(injson)

    #Capture current step
    logger.info("json file found. Institution parameters read in.")
    
    #Write parameters for debugging
    logger.debug("Parameters: %s"%parameters)

    #Return parameters list
    return parameters

def write_json(MDFit_path):
    #Template data to write to json file
    dictionary = {
        "hostnames": {
            "FFBUILDER":"localhost",
            "BMIN":"localhost",
            "MULTISIM":"localhost",
            "DESMOND":"localhost-gpu",
            "ANALYSIS":"localhost"
        },
        "parameters": {
            "MAXLIGS":100,
            "FFPROC":32
        }
    }

    #Convert dictionary to json object
    json_object = json.dumps(dictionary, indent=4)

    #Open template json file for writing
    with open(os.path.join(MDFit_path, "parameters_TEMPLATE.json"), "w") as outfile:
        #Write lines to json file
        outfile.write(json_object)
    
    #Capture current step
    logger.critical("Edit the %s file and rename to %s"%(os.path.join(MDFit_path, "parameters_TEMPLATE.json"), os.path.join(MDFit_path, "parameters.json")))

def main(MDFit_path):
    #Check if json file exists
    if os.path.isfile(os.path.join(MDFit_path, "parameters.json")) == True:
        #If it does, read in parameters
        inst_params = read_json(MDFit_path)
    
    #json file does not exist
    else:
        #Check if template exists
        if os.path.isfile(os.path.join(MDFit_path, "parameters_TEMPLATE.json")) == True:
            #If it does, print path to template for user
            logger.critical("Parameter template file found: %s"%(os.path.join(MDFit_path, "parameters_TEMPLATE.json")))

            #Print path needed for user
            logger.critical("Rename to: %s"%(os.path.join(MDFit_path, "parameters.json")))
        
        #Template file does noto exist
        else:
            #Write out template for user to edit
            write_json(MDFit_path)

        #Print to screen
        print("Parameters not found. Information captured in MDFit.log")

        #Exit
        sys.exit()

    #Return parameters
    return inst_params

if __name__ == '__main__':
    main(MDFit_path)