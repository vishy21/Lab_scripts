#!/usr/bin/python

import os
import SEARCH_zipimport as S_zi
import logging


'''
!! Run locally, we need certain packages that are not installed on Singularity or ICore !!
 
Change the input_dir to the location of the .zip files imported off FTP from SEARCH team

Run: python do_import.py
	
Outputs:
 	1. Unzips the zip files
 	2. Checks if DICOM header information matches the recorded pidn/visit in the filename
	3. Moves to the SEARCH R drive location: *** REQUIRES USER CONFIRMATION TO PROCEED ***
		a. 8 MRI sequences: Sag.T1W.3D, Ax TSE, Ax FLAIR, DTI, DTIb0, rsfMRI, 2 MRS screenshots
		b. 8 MRS files if present: 4 .spar, 4 .sdat
	4. Outputs a log into the input directory with record of mismatches and missing scans if any


Files required: SEARCH_zipimport.py


Original Author:
Kevin Chang 07/2018


Revisions:
'''

###################################################################################################################
###################################################################################################################


# Directory with the compressed files inside
input_dir = os.path.join("C:",os.sep, "Users","sf287610","Desktop","Compressed_Scans","SEARCH_replacements")

# Initialize the logger
logging.basicConfig(filename = os.path.join(input_dir,"importer.log"), level=logging.DEBUG)

# Run the zip import steps
scan_holder = S_zi.run_import_steps(input_dir)
S_zi.run_archive_steps(scan_holder, input_dir)
S_zi.create_output_logs(scan_holder, input_dir)