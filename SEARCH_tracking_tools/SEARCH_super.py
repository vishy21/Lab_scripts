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
import subprocess
import logging


'''
Contains functions and classes needed for SEARCH_run.py to function
Current functions and classes:
	csv reader
	DICOM reader and scan parameter check
	sequence parse
	SEARCH_object class
		holds study, PIDN, visit, file locations, etc

Currently implemented scanners: Ingenia, Achieva (3T Philips)
Currently implemented studies:
	SEARCH 010 (S010)
	SEARCH 013 (S013A and S013B)
	SEARCH 023 RV405 (T11)
	SEARCH 010 RV398 (S398)


To Do:
	Streamline exporting so we can select only certain scan types to export
	Export specific scans as zip files to reduce size
	Take another look at dicom header checks to make sure that we catch typos
	Move from print statements to using logging package




Original Author:
Kevin Chang 2018/07


Revisions:
	2018/07/25 - KCC: Added function for exporting fMRI and T1 NIFTI formats for WUSTL use
	2018/11/26 - KCC: Edited code to accept "MRS for Pom" as well as "MRS" as MRS locations
'''


###################################################################################################################
###################################################################################################################

log_dir = os.path.join("R:",os.sep,"groups","valcour","kevin","test_files_for_scripts","BK_tracking_test")
logging.basicConfig(filename = os.path.join(log_dir,"debug.log"), level=logging.DEBUG)

R_SEARCH_archive_loc = os.path.join("R:",os.sep,"groups","valcour","SEARCH")

def create_obj_from_csv(csvinput):
	# Reads and creates class from a csv input
	# Format: Study | PIDN | Visit 
	input_df = pd.read_csv(csvinput)
	print "\n"
	print "---------------------"
	print "READING INPUT CSV "
	print "---------------------"
	#return input_df
	#print input_df
	d_subj = {}
	counter = 0
	for i in input_df.index:
		try:
			d_subj[i] = SEARCH_object(input_df.loc[i,"Study"],input_df.loc[i,"PIDN"],input_df.loc[i,"Visit"])
			if d_subj[i].exists == False:
				print "ERROR: COULD NOT FIND", d_subj[i].study, d_subj[i].PIDN, d_subj[i].visit
				del(d_subj[i])
				counter += 1
		except:
			#print "ERROR AT %s INDEX" % i
			print "ERROR READING \n%s, INDEX %s" %(input_df.loc[i,["PIDN","Visit"]],i)
			counter += 1
			pass
	print "%s subjects read" % len(d_subj)
	if counter > 0:
		print "WARNING: %s subject(s) could not be parsed!!" % counter
	print ""

	return d_subj


def parse_sequence(sequence_name):
	# currently only for ingenia and achieva scanners at BK

	T1_pattern = re.compile("Sag.T1W.3D")
	T1_exclude =re.compile("Sag.T1W.3D.*3mm")
	TSE_pattern = re.compile("TSE")
	FLAIR_pattern = re.compile("FLAIR")
	DTI2_pattern = re.compile("DTI.2.2.2")
	DTIb_pattern = re.compile("DTI.b0")
	fMRI_pattern = re.compile("F+E.EPI")
	MRS_pattern = re.compile("MRS")


	if T1_pattern.search(sequence_name) and not T1_exclude.search(sequence_name):
		return "T1"
	elif TSE_pattern.search(sequence_name):
		return "TSE"
	elif FLAIR_pattern.search(sequence_name):
		return "FLAIR"
	elif DTI2_pattern.search(sequence_name):
		return "DTI"
	elif DTIb_pattern.search(sequence_name):
		return "DTIb0"
	elif fMRI_pattern.search(sequence_name):
		return "fMRI"
	elif MRS_pattern.search(sequence_name):
		return "MRS"
	else:
		return sequence_name


def scan_params_QA(header, sequence_type):
	results = {}
	if sequence_type in ["T1","FLAIR","DTI","DTIb0","fMRI"]:
		try:
			#
			results["TE"] = header.PerFrameFunctionalGroupsSequence[0][8197,5135][0].EchoTime
			results["TR"] = header.SharedFunctionalGroupsSequence[0].MRTimingAndRelatedParametersSequence[0].RepetitionTime

			SliceThickness = header.PerFrameFunctionalGroupsSequence[0][8197,5135][0].SliceThickness
			Pixel_size = header.PerFrameFunctionalGroupsSequence[0][8197,5135][0].PixelSpacing
			results["Voxel"] = [Pixel_size[0],Pixel_size[1],SliceThickness]
			
			results["Slices"] = header.NumberOfFrames
			results["Slice_spacing"] = header.PerFrameFunctionalGroupsSequence[0][8197,5135][0].SpacingBetweenSlices - SliceThickness
			results["AcquisitionTime"] = header.AcquisitionDuration/60
			

			if sequence_type == "T1":
				results["Flip"] = header.SharedFunctionalGroupsSequence[0].MRTimingAndRelatedParametersSequence[0].FlipAngle

			if sequence_type == "FLAIR":
				results["TI"] = header.InversionTime

			if sequence_type == "DTI" or sequence_type == "DTIb0":
				results["N_avg"] = header.PerFrameFunctionalGroupsSequence[0][8197,5135][0].NumberOfAverages
				results["FOV"] = [header.Rows, header.Columns]
				results["Parallel_factor"] = "%s: %s" % (header.ParallelAcquisitionTechnique, header.ParallelReductionFactorInPlane)
				results["EPI_factor"] = header.PerFrameFunctionalGroupsSequence[0][8197,5135][0].EchoTrainLength
				#results["Directions"] = 32 # STILL NEED TO FIND IN DICOM HEADER
				results["b_val"] = header.PerFrameFunctionalGroupsSequence[1].MRDiffusionSequence[0].Diffusionbvalue



			return results
		except Exception as e:
			raise e
	else:
		return False

def make_log(holder):
	#pass
	csv_export_loc = os.path.join("R:",os.sep,"groups","valcour","kevin","Lab_scripts","SEARCH_tracking_tools","test_output.csv")
	df = pd.DataFrame()
	for j in holder:
		i = holder[j]
		if i.MRS_files == 1 and i.MRS_count == 8:
			mrs_temp = 1
		else:
			mrs_temp = 0

		if i.mri_exists == False:
			i.headerdata = {}
			i.headerdata["PatientID"] = False
			i.headerdata["Date"] = False
			i.headerdata["Age"] = False
			i.headerdata["Gender"] = False
			i.headerdata["ScanType"] = False
			i.headerdata["Scanner"] = False
			i.T1 = False
			i.TSE = False
			i.FLAIR = False
			i.DTI = False
			i.DTIb0 = False
			i.fMRI = False
			i.MRS = False
			i.other = False
			





		df_temp = pd.DataFrame([[i.study, i.PIDN,i.visit, i.headerdata["Date"], i.headerdata["Age"],i.headerdata["Gender"], i.headerdata["Scanner"], i.T1, i.FLAIR, i.TSE, i.DTI, i.DTIb0, i.fMRI, i.MRS, mrs_temp ]],
			columns = ["Study","PIDN","Visit","Date","Age","Gender","Scanner","T1","FLAIR","TSE","DTI","DTIb0","fMRI","MRS srcnshot","MRS Files"])
		df = df.append(df_temp)
		del mrs_temp, df_temp
	df.to_csv(csv_export_loc, index=False)




class SEARCH_object:
	def __init__(self, study, pidn, visit):

		### READ THE STUDY, PIDN, AND VISIT CODES ###
		self.study = study.strip()
		if pidn[0] != "P" and self.study == "S010":
			self.PIDN = "P"+pidn.strip()
		elif pidn[0] != "P" and self.study == "T11":
			self.PIDN = "P" + pidn.strip()
		else:
			self.PIDN = pidn.strip()
		self.visit = visit.strip()

		### GET LOCATION OF FILES ON R DRIVE ###
		self.R_location = self.get_R_loc()
		logging.debug(self.R_location)
		if self.R_location:
			if os.path.isdir(self.R_location):
				self.exists = True

			else:
				self.exists = False
		else:
			self.exists = False
			print "ERROR: %s DOES NOT EXIST" % self.R_location


		## MRS status ##
		self.MRS_files = 0
		self.MRS_count = 0


		## MRI status ##
		self.mri_files = False

		self.scan_params={}


	def get_R_loc(self):
		logging.info("%s %s %s" % (self.study, self.PIDN, self.visit))
		if self.study == "S010":
			return os.path.join(R_SEARCH_archive_loc,"SEARCH010","{0.study}.{0.PIDN}{sep}{0.study}.{0.PIDN}_{0.visit}".format(self, sep = os.sep))

		elif self.study == "S013":
			if self.PIDN[-1] == "A":
				return os.path.join(R_SEARCH_archive_loc,"SEARCH013","Controls",self.PIDN,self.visit)
			elif self.PIDN[-1] == "B":
				return os.path.join(R_SEARCH_archive_loc,"SEARCH013",self.PIDN,self.visit)

		elif self.study == "T11":
			return os.path.join(R_SEARCH_archive_loc,"SEARCH023 RV405","{0.study}.{0.PIDN}{sep}{0.study}.{0.PIDN}_{0.visit}".format(self, sep = os.sep))
				
		elif self.study == "S398":
			return os.path.join(R_SEARCH_archive_loc, "SEARCH RV398", "{0.study}_04_{0.PIDN}{sep}{0.study}_04_{0.PIDN}_{0.visit}".format(self, sep = os.sep) )

		elif self.study == "S025":
			return os.path.join(R_SEARCH_archive_loc,"SEARCH025","{0.study}.{0.PIDN}{sep}{0.study}.{0.PIDN}_{0.visit}".format(self, sep = os.sep))
		
		else:
			print "STUDY CODE NOT YET IMPLEMENTED..."
			return False

	def check_files(self):
		if self.exists:
			R_dirs = os.listdir(self.R_location)
			#print R_dirs
			
			mri_path = [tmpmri for tmpmri in R_dirs if tmpmri.startswith("mri_images")]
			if mri_path:
				self.mri_dir = os.path.join(self.R_location, mri_path[0])
				if not os.path.isdir(self.mri_dir):
					self.mri_exists = False
					print self.PIDN, self.visit, "is missing mri_images"
				else:
					self.mri_exists = True
			else:
				self.mri_exists = False



			mrs_path = [tmpmrs for tmpmrs in R_dirs if tmpmrs.startswith("MRS")]
			if mrs_path:
				self.MRS_dir = os.path.join(self.R_location, mrs_path[0])
				if not os.path.isdir(self.MRS_dir):
					self.MRS_exists = False
					print self.PIDN, self.visit, "is missing MRS dir"
				else:
					self.MRS_exists = True
			else:
				self.MRS_exists = False


			pass

	def do_MRS_export(self, export_loc):
		# For Exporting the .spar and .sdat files to Pom
		pass
		now = datetime.now()
		date = now.strftime("%Y-%m-%d")
		ignore_zip = shutil.ignore_patterns('*.zip')
		count = 0
		if self.MRS_exists:
			self.dir2create = os.path.join(export_loc,"MRSforPom_%s" % date, "{0.study}{sep}{0.study}.{0.PIDN}_{0.visit}".format(self,sep=os.sep) )
			os.makedirs(self.dir2create)
			for mrs_file in os.listdir(self.MRS_dir):
				if re.search("spar""|""sdat", mrs_file, re.IGNORECASE):
					shutil.copy(os.path.join(self.MRS_dir,mrs_file), self.dir2create)
					count += 1

			print "EXPORTING %s FILES TO %s" % (count, self.dir2create)


		else:
			print "ERROR: No MRS directory found for {0.study}.{0.PIDN}_{0.visit}".format(self,sep=os.sep)

		return os.path.join(export_loc,"MRSforPom_%s" % date)


	def do_fMRI_export(self,export_loc):
		# For exporting fMRI and T1 as nifti files for Carissa at WUSTL
		pass
		now = datetime.now()
		date = now.strftime("%Y-%m-%d")
		ignore_zip = shutil.ignore_patterns('*.zip')
		if self.mri_dir:
			self.dir2create = os.path.join(export_loc,"%s_export" % date, "{0.study}{sep}{0.study}.{0.PIDN}_{0.visit}".format(self,sep=os.sep))
			os.makedirs(self.dir2create)
			for modality in ["Sag.T1W.3D","Ax FFE.EPI"]:
				export2 = os.path.join(self.dir2create, modality)
				export_from = os.path.join(self.mri_dir, modality)
				print export2
				print export_from

				os.makedirs(export2)

				if os.path.isdir(export_from):
					pass
					print "NOT IMPLEMENTED YET, NO dcm2nii CMD ON LOCAL MACHINE"

				else:
					print "ERROR, COULD NOT FIND DIRECTORY FOR %s %s %s %s" % (self.study, self.PIDN, self.visit, modality)
					print "CURRENTLY ONLY EXPORTS FROM <Sag.T1W.3D> and <Ax FFE.EPI> NAMED DIRECTORIES"

		return os.path.join(export_loc,"%s_export" % date)


	def do_full_zip_export(self,export_loc,pattern2ignore=None):
		# For exporting the entire pidn/visit file as a zip
		pass
		#print export_loc
		now = datetime.now()
		date = now.strftime("%Y-%m-%d")

		if self.exists:
			event_name = "{0.study}{sep}{0.study}.{0.PIDN}_{0.visit}".format(self,sep=os.sep) 
			self.dir2create = [os.path.join(export_loc, "%s_export" % date, event_name)]
			print "EXPORTING", self.PIDN, self.visit
			shutil.make_archive(self.dir2create[0],"zip",self.R_location)
		else:
			print "ERROR"

		return os.path.join(export_loc, "%s_export" % date)








	def check_dicoms(self, check_params=True, export = False):
		### Want to record:
		### - PatientName (pid)
		### - Date
		### - Age
		### - Gender
		### - Scan Type
		### - Scanner
		now = datetime.now()
		date = now.strftime("%Y-%m-%d")
		if export == True:
			export_loc = os.path.join("R:",os.sep,"groups","valcour","kevin","SEARCH_%s" % date)
			os.makedirs(self.export_loc)




		if self.mri_exists:
			self.headerdata = {}
			self.headerdata["PatientID"] = set()
			self.headerdata["Date"] = set()
			self.headerdata["Age"] = set()
			self.headerdata["Gender"] = set()
			self.headerdata["ScanType"] = set()
			self.headerdata["Scanner"] = set()

			out_msg = "READING DICOMS IN %s" % self.R_location
			print "\n"
			print "-"*len(out_msg)
			print out_msg
			print "-"*len(out_msg)

			for root,dirs,files in os.walk(self.R_location):
				if files:
					for file in files:
						# If file is nifti or analyze, skip
						if os.path.splitext(file)[1] in [".nii",".hdr",".img"]:
							pass

						# If file is MRS, record
						elif re.search("spar""|""sdat", file, re.IGNORECASE):
							self.MRS_files = 1
							self.MRS_count += 1

						# If not MRS, then try reading dicom header
						else:
							try:
								dicom_loc = os.path.join(root, file)
								# if we want to check params, then we need pixel data; else, we can skip
								if check_params:
									header = dicom.read_file(dicom_loc)
								else:
									header = dicom.read_file(dicom_loc, stop_before_pixels = True)
							except:
								print "DICOM READ ERROR AT %s" % file
							else:
								try:
									self.headerdata["PatientID"].add(header.PatientName)
								except:
									pass
								try:
									self.headerdata["Date"].add( datetime.strftime( datetime.strptime(header.StudyDate, '%Y%m%d'), '%Y-%m-%d' ))
								except:
									pass
								try:
									self.headerdata["Age"].add(header.PatientAge)
								except:
									pass
								try:
									self.headerdata["Gender"].add(header.PatientSex)
								except:
									pass
								try:
									self.headerdata["ScanType"].add(header.SeriesDescription)
									read_temp = parse_sequence(header.SeriesDescription)
									if check_params and header.PixelData and read_temp in ["T1","FLAIR","DTI","DTIb0","fMRI"]:
										self.scan_params[read_temp] = scan_params_QA(header,read_temp)
								except:
									pass
								try:
									if header.ManufacturerModelName == "Ingenia":
										self.headerdata["Scanner"].add("3T Philips Ingenia")
									else:
										self.headerdata["Scanner"].add(header.ManufacturerModelName)
								except:
									pass



			self.scans = [parse_sequence(scann) for scann in self.headerdata["ScanType"]]
			self.T1 = self.scans.count("T1")
			self.TSE = self.scans.count("TSE")
			self.FLAIR  = self.scans.count("FLAIR")
			self.DTI  = self.scans.count("DTI")
			self.DTIb0  = self.scans.count("DTIb0")
			self.fMRI  = self.scans.count("fMRI")
			

			#self.MRS  = self.scans.count("MRS")
			if self.scans.count("MRS") == 2:
				self.MRS = 1
			else:
				self.MRS = 0


			self.other  = len(self.scans)-(self.T1+self.TSE+self.FLAIR+self.DTI+self.DTIb0+self.fMRI+self.scans.count("MRS"))

			print self.T1, self.TSE, self.FLAIR, self.DTI, self.DTIb0, self.fMRI, self.MRS, self.other, self.MRS_count
			for i in self.headerdata:
				self.headerdata[i] = ",".join(list(self.headerdata[i]))
			print self.headerdata
			pprint(self.scan_params)












