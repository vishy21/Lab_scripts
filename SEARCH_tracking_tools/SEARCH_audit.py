#!/usr/bin/python
import os
import numpy as np 
import pandas as pd 
import dicom
import re
import sys

###########################
# Run as SEARCH_audit.py STUDYCODE INPUTCSV
# Input a study code and a csv file with columns:
# PIDN | Visit
#
# The script will search through the directory to see if the files exist as expected
#
###########################

#input_studycode = raw_input("ENTER STUDY CODE:")
#input_file = raw_input("ENTER CSV FILE LOCATION:")

########### READ INPUTS ##############

if sys.argv[1]:
	input_studycode = sys.argv[1]
	if input_studycode in ["S010","SEARCH010"]:
		print "STUDY CODE READ AS SEARCH010"
		study_code = "SEARCH010"
	elif input_studycode in ["S013","SEARCH013"]:
		print "STUDY CODE READ AS SEARCH013"
		study_code = "SEARCH013"
	elif input_studycode in ["RV398","S398","SEARCH010 RV398"]:
		print "STUDY CODE READ AS SEARCH010 RV398"
		study_code = "SEARCH RV398"
	elif input_studycode in ["S023","S23","T11","SEARCH023"]:
		print "STUDY CODE READ AS SEARCH023 (T11)"
		study_code = "SEARCH023 RV405"
	else:
		print "STUDY CODE UNKNOWN"
		print "CURRENTLY IMPLEMENTED: S010,S013,S398,T11"
		study_code = False
else:
	print "STUDY CODE MISSING OR MISFORMATTED"
	study_code = False

if sys.argv[2]:
	input_file = sys.argv[2]
	input_df = pd.read_csv(input_file)

if study_code:
	path1 = os.path.join("R:","groups","valcour","SEARCH",study_code)
	print "Seeking directories within %s" % path1
	try:
		os.chdir(path1)
		print "==========================================="
		checkpoint1 = True
	except Exception as e:
		raise e


if checkpoint1:
	for i in input_df.index:
		PIDN = input_df.iloc[i,0]
		visit = input_df.iloc[i,1]
		print "CHECKING PIDN %s VISIT %s" % (PIDN, visit)
		if study_code = "SEARCH010":
			



