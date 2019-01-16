#!/usr/bin/python

import pandas as pd
import os
import numpy as np
import dicom
import re
import xlsxwriter
import datetime
from datetime import datetime
from pprint import pprint
import shutil
from zipfile import ZipFile

#
# To Run: Change the location of the tracking sheet, then run > python redcap_proc.py
# 
# This script takes the tracking sheet we have at UCSF and converts it into a csv file to Jennifer Chiarella <jennifer.chiarella@yale.edu>
# Jen will then process it and use it to update the Yale redcap records
# 
# Inputs:
#	tracking sheet location
#	output location
# 
# Outputs:
# 	csv file with redcap formatted data
#
# To Do:
#	
#	
# 
#
# Original Author:
# Kevin Chang 07/2018
#
# Revisions:
#	09/2018: KCC; updated to bring in line with new tracking sheet conventions, options for Ingenia only vs all
#

now = datetime.now()
date = now.strftime("%Y-%m-%d")


updated_tracking_sheet = os.path.join("H:",os.sep,"Research","HIV Protocols","04 Projects","02 SEARCH","SEARCH General","05 Data and Analyses","MRI and MRS data tracking","SEARCH_UCSF_new_tracking.xlsm")
old_output = os.path.join("R:",os.sep,"groups","valcour","kevin","Lab_scripts","SEARCH_tracking_tools","redcap_output_2018-09-11.csv")
output_loc = os.path.join("R:",os.sep,"groups","valcour","kevin","Lab_scripts","SEARCH_tracking_tools","redcap_output_%s.csv" % date)


###################################################################################################################
###################################################################################################################


tracking_df = pd.read_excel(updated_tracking_sheet,sheet_name="S010")

#print tracking_df.shape
#print tracking_df.columns[0]
output_df = pd.DataFrame(columns=["patientid","redcap_event_name","mri_machine","mri_date","mri_t1","mri_t2","mri_dti","mri_rsfmri","mri_mrs","mri_tracking_from_jd_complete"])
# patientid = PIDN
# event name = visit parsed into M/W/V
# mri_machine = 1 for 1.5T GE
#				2 for 3T Achieva
#				3 for 3T Ingenia
# 				blank for others
# scans: 1 for present, 0 for not
# mri_tracking = 2 for complete

def visit_parse(monthcode):
	if monthcode.strip() == "M0":
		return "m0w0v01baseline_arm_1"
	elif monthcode.strip() == "M1":
		return "m1w4v08_arm_1"
	elif monthcode.strip() == "M3":
		return "m3w12v10_arm_1"
	elif monthcode.strip() == "M6":
		return "m6w24v13_arm_1"
	elif monthcode.strip() == "M9":
		return "m9w36v14_arm_1"
	elif monthcode.strip() == "M12":
		return "m12w48v15_arm_1"
	elif monthcode.strip() == "M18":
		return "m18w72v17_arm_1"
	elif monthcode.strip() == "M24":
		return "m24w96v19_arm_1"
	elif monthcode.strip() == "M36":
		return "m36w144v23_arm_1"
	elif monthcode.strip() == "M48":
		return "m48w192v27_arm_1"
	elif monthcode.strip() == "M60":
		return "m60w240v31_arm_1"
	elif monthcode.strip() == "M72":
		return "m72w288v35_arm_1"
	elif monthcode.strip() == "M84":
		return "m84w336v39_arm_1"
	elif monthcode.strip() == "M96":
		return "m96w384v43_arm_1"
	elif monthcode.strip() == "M108":
		return "m108w432v47_arm_1"


def machine_parse(scanner):
	if scanner == "1.5 GE Signa Excite":
		return 1
	elif scanner == "3T Philips Achieva":
		return 2
	elif scanner == "3T Philips Ingenia":
		return 3
	else:
		return None




for event in tracking_df.index:
	print tracking_df.loc[event, "Date"]
	# DO Ingenia Only
	if True:
		if tracking_df.loc[event, "Scanner"] == "3T Philips Ingenia":
			output_df.loc[event,"patientid"] = tracking_df.loc[event, "PIDN"]
			output_df.loc[event,"redcap_event_name"] = visit_parse(tracking_df.loc[event, "Visit"])
			output_df.loc[event,"mri_machine"] = machine_parse(tracking_df.loc[event, "Scanner"])
			output_df.loc[event,"mri_date"] = tracking_df.loc[event,"Date"].strftime("%Y-%m-%d")
			output_df.loc[event,"mri_t1"] = tracking_df.loc[event, "T1"]
			output_df.loc[event,"mri_t2"] = tracking_df.loc[event, "FLAIR"]
			output_df.loc[event,"mri_dti"] = tracking_df.loc[event, "DTI"]
			output_df.loc[event,"mri_rsfmri"] = tracking_df.loc[event, "fMRI"]
			output_df.loc[event,"mri_mrs"] = tracking_df.loc[event, 'MRS files']
			output_df.loc[event,"mri_tracking_from_jd_complete"] = 2

	# DO ALL
	if False:
		output_df.loc[event,"patientid"] = tracking_df.loc[event, "PIDN"]
		output_df.loc[event,"redcap_event_name"] = visit_parse(tracking_df.loc[event, "Visit"])
		output_df.loc[event,"mri_machine"] = machine_parse(tracking_df.loc[event, "Scanner"])
		output_df.loc[event,"mri_date"] = tracking_df.loc[event,"Date"].strftime("%Y-%m-%d")
		output_df.loc[event,"mri_t1"] = tracking_df.loc[event, "T1"]
		output_df.loc[event,"mri_t2"] = tracking_df.loc[event, "FLAIR"]
		output_df.loc[event,"mri_dti"] = tracking_df.loc[event, "DTI"]
		output_df.loc[event,"mri_rsfmri"] = tracking_df.loc[event, "fMRI"]
		output_df.loc[event,"mri_mrs"] = tracking_df.loc[event, 'MRS files']
		output_df.loc[event,"mri_tracking_from_jd_complete"] = 2

output_df.to_csv(output_loc,index=False)



