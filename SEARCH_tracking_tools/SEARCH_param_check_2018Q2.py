#!/usr/bin/python

import SEARCH_super as s
import os

#############################################

csv_name = "2018_Q3_paramcheck.csv"
#csv_location = os.path.join("R:",os.sep,"groups","valcour","kevin","test_files_for_scripts","BK_tracking_test","2018Q3_paramcheck.csv")
csv_location = os.path.join("C:",os.sep,"Users","sf287610","Documents","01 SEARCH","09 Work Notes",csv_name)
#csv_location = os.path.join("R:",os.sep,"groups","valcour","kevin","Lab_scripts","SEARCH_tracking_tools","S010_3T_test.csv")


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
