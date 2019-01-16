#!/usr/bin/python

import SEARCH_super as s
import os
import shutil
import datetime


#
# To Run: change the location variables as necessary, set True/False for which parts to perform and run > python SEARCH_run.py
#
# Files required: SEARCH_super.py
#
# Inputs:
# 	csv_location: csv file with the columns study, PIDN, visit in that order
# 	export_location: if exporting scans to another location, specify that here
#
#
# See SEARCH_super.py for more detailed explanation on how these work
# 
#
#
# Original Author:
# Kevin Chang 2018-07
#
# Revisions:
#	2018/07/25 - KCC: Added fMRI export lines, WIP
#

###################################################################################################################
###################################################################################################################

now = datetime.datetime.now()

#csv_location = os.path.join("R:",os.sep,"groups","valcour","kevin","Lab_scripts","SEARCH_tracking_tools","export_2018-07-19.csv")
#csv_location = os.path.join("R:",os.sep,"groups","valcour","kevin","Lab_scripts","SEARCH_tracking_tools","MRS_export_test.csv")
csv_location = os.path.join("C:",os.sep,"Users","sf287610","Desktop","Compressed_Scans","mrs_export_20181129.csv")

export_location = os.path.join("C:",os.sep,"Users","sf287610","Desktop","Compressed_Scans")


##############	MUST RUN THIS PART!	##################
subjects = s.create_obj_from_csv(csv_location)
for sub in subjects:
	subjects[sub].check_files()



###########	CHECK DICOMS? #######################
if False:
	for sub in subjects:
		subjects[sub].check_dicoms(check_params = False, export = False)

if False:
	s.make_log(subjects)


########## EXPORT OPTIONS #######################

# 3T MRS for Pom
if True:
	pass
	for sub in subjects:
		# do copy
		MRS_exporter = subjects[sub].do_MRS_export(export_location)
	shutil.copy(csv_location,MRS_exporter)

# 3T fMRI for carissa
if False:
	pass
	for sub in subjects:
		fMRI_exporter = subjects[sub].do_fMRI_export(export_location)
	shutil.copy(csv_location,fMRI_exporter)




# 3T MRI
if False:
	pass
	# which modalities to 



# FULL FOLDER ZIPPED
if False:
	pass

	for sub in subjects:
		# do copy
		full_exporter = subjects[sub].do_full_zip_export(export_location)
	shutil.copy(csv_location, full_exporter)






	# DO COPY TO WORKING FOLDER
#############################################
