#!/usr/bin/python

import SEARCH_super as s
import os


# !! Run locally, we need certain packages that are not installed on Singularity or ICore !!
# 
# Change the csv_name to the name of the csv with study | pidn | visit to check parameters for
# Currently requires running Jupyter notebook script to build the csv
#
# Run: python SEARCH_QA_paramchecker.py
#	
# Outputs:
#	1. csv log with the parameters that we are interested in
#
#
# Files required: SEARCH_super.py, jupyter notebook <SEARCH QA scripts>
#
# To do:
# 	Move the jupyter code here so it can all be run at once
#
#
# Original Author:
# Kevin Chang 2018/07
#
#
# Revisions:
#	2018/10/03 - KCC: Generalized the code for future usage
#
###################################################################################################################
###################################################################################################################

year2check = 2018
quarter2check = "Q4"
csv_name = "%s_%s_paramcheck.csv" %(year2check,quarter2check)
csv_location = os.path.join("C:",os.sep,"Users","sf287610","Documents","01 SEARCH","09 Work Notes",csv_name)


#############################################


subjects = s.create_obj_from_csv(csv_location)
for sub in subjects:
	subjects[sub].check_files()

if True:
	for sub in subjects:
		subjects[sub].check_dicoms(check_params = True, export = False)

if False:
	s.make_log(subjects)


if False:
	pass
	for sub in subjects:
		# do copy
		pass
	# DO COPY TO WORKING FOLDER
#############################################
