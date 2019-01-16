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

########################################
#
# Archive architecture:
# S010: SEARCH/SEARCH010/S010.P####/S010.P****_M**/
# S013A:
# S013B:
# 
#
#
#
#########################################

def csv_read(csvinput):
	input_df = pd.read_csv(csvinput)
	#return input_df
	#print input_df
	d_subj = {}
	for i in input_df.index:
		d_subj[i] = SEARCH_subject(input_df.loc[i,"Study"],input_df.loc[i,"PIDN"],input_df.loc[i,"Visit"])
	return d_subj



def test_fn(inputs):
	print inputs



class SEARCH_subject:
	def __init__(self, study, pidn, visit):
		self.PIDN = pidn
		self.study = study
		self.visit = visit
		self.base_location = os.path.join("R:",os.sep,"groups","valcour","SEARCH")
		self.dir = self.base_location
		self.error_log = []
		self.in_Rdrive = False

	def get_loc(self):
		# Standardize PIDN and study formats
		self.dir = self.parse_study()
		if self.dir:
			if os.path.isdir(self.dir):
				self.in_Rdrive = True
			
			print self.dir
			print self.in_Rdrive
			print os.listdir(self.dir)


		else:
			print "Study %s is not currently supported or is input incorrectly."
			print "Currently implemented: S010, S013, T11, S398, S018"
			self.error_log.append("Input study could not be parsed")

	def do_3T_audit(self):
		# Check archive for our participants with 3T files
		# Check for 1: are the directories set up as expected?
		#			2: which scans are stored in dicoms
		#			3: if MRS screenshot is there, are MRS files present?

		if self.in_Rdrive:
			self.mri_dir = os.path.join(self.dir, "mri_images")
			self.MRS_dir = os.path.join(self.dir, "MRS")

			if os.path.isdir(self.mri_dir):
				for root, dirs, files in os.walk(self.mri_dir):
					if files:
						print root, dirs, files


				pass
			else:
				self.error_log.append("mri_images at %s is missing" % self.mri_dir)
				print "%s could not be found" % self.mri_dir

	def dicom_header_import(self,root,dcmfile):
		dicom_loc = os.path.join(root, dcmfile)
		try:
			header = dicom.read_file(dicom_loc)
		except:
			header = None
			print "ERROR READING: %s" % dicom_loc
		#print "reading: ",dcmfile
		# reset dataframes for each dicom
		try:
			dicom_name = header.PatientName
		except:
			dicom_name = "ERROR"
		try:
			pAcqDate = header.StudyDate
		except:
			pAcqDate = "N/A"
		try:
			pSex = header.PatientSex
		except:
			pSex = "N/A"
		try:
			pAge = header.PatientAge
		except:
			pAge = "N/A"
		try:
			pScanner = header.ManufacturerModelName
		except:
			pScanner = "N/A"
		try:
			pSeq = header.SeriesDescription
		except:
			pSeq = "N/A"
		
		# read dicom_name to see if matches study, PIDN, visit
		if re.search(self.study,dicom_name):
			self.dcmheader.loc[0,"Study"] = self.study
		else:
			self.dcmheader.loc[0,"Study"] = "CHECK HEADER"
			self.QA_notes.append("Study mismatch in dicom header; ")
		if re.search(self.PIDN,dicom_name):
			self.dcmheader.loc[0,"PIDN"] = self.PIDN
		else:
			self.dcmheader.loc[0,"PIDN"] = "CHECK HEADER"
			self.QA_notes.append("PIDN mismatch in dicom header; ")
		if re.search(self.visit,dicom_name):
			self.dcmheader.loc[0,"Visit"] = self.visit
		else:
			self.dcmheader.loc[0,"Visit"] = "CHECK HEADER"
			self.QA_notes.append("Visit mismatch in dicom header; ")


		if self.dcmheader.loc[0,"AcquisitionDate"] == "":
			self.dcmheader.loc[0,"AcquisitionDate"] = pAcqDate
		elif self.dcmheader.loc[0,"AcquisitionDate"] != pAcqDate:
			self.QA_notes.append("AcqDate mismatch in dicom header; ")


		if self.dcmheader.loc[0,"PatientAge"] == "":
			self.dcmheader.loc[0,"PatientAge"] = pAge
		elif self.dcmheader.loc[0,"PatientAge"] != pAge:
			self.QA_notes.append("Age mismatch in dicom header; ")


		if self.dcmheader.loc[0,"PatientSex"] == "":
			self.dcmheader.loc[0,"PatientSex"] = pSex
		elif self.dcmheader.loc[0,"PatientSex"] != pSex:
			self.QA_notes.append("Sex mismatch in dicom header; ")


		if self.dcmheader.loc[0,"ScannerID"] == "":
			self.dcmheader.loc[0,"ScannerID"] = pScanner
		elif self.dcmheader.loc[0,"ScannerID"] != pScanner:
			self.QA_notes.append("Scanner mismatch in dicom header; ")


		
		if pScanner in known_3T_scanners and "PixelData" in header:
			scan_type = parse_sequence(pSeq)
			# scan_type returns [scan name to be tracked under, directory to be saved in]
			if scan_type != False:
				self.save_dir = os.path.join( self.mri_dir, scan_type[1])
				if not os.path.isdir(self.save_dir):
					os.makedirs( self.save_dir )
				self.save_location = os.path.join(self.save_dir,"%s.dcm" % dcmfile)
				print "%s READ AS %s, SAVING TO %s" % (dcmfile, scan_type[0],self.save_location)
				#print dcmfile
				#print "%s FOUND, SAVING TO %s" % (scan_type[0],save_location)
				header.save_as(self.save_location)
				self.dcmheader.loc[0,scan_type[0]] += 1
			else:
				self.dcmheader.loc[0,"Other"].append(pSeq)

		elif pScanner in known_3T_scanners and not ("PixelData" in header):
			print "WARNING: %s is not an image" % dcmfile
		elif pScanner not in known_3T_scanners:
			print "WARNING: %s/%s is scanned on %s, automatic processing not implemented!" % (root,dcmfile,pScanner)
			self.QA_notes.append("Not auto-processed due to scanner name; ")
		else:
			#print "No image at %s/%s" % (root,dcmfile)
			pass

		
		
		
		# reset variables
		del header, dicom_name, pAcqDate,pSex,pAge,pScanner,pSeq


	def parse_study(self):
		if self.study == "S010":
			# S010 pidn should be PXXXX, not XXXX
			if self.PIDN[0] != "P":
				self.PIDN = "P" + self.PIDN
			return os.path.join(self.base_location,"SEARCH010","%s.%s" % (self.study, self.PIDN), "%s.%s_%s" % (self.study, self.PIDN, self.visit))
			
		elif self.study == "S013":

			# S013 pidn should not have leading P
			if self.PIDN[0] == "P":
				self.PIDN = self.PIDN[1:]
			if self.PIDN[-1] == "A":
				# S013 Control
				return os.path.join(self.base_location,"SEARCH013","Controls",self.PIDN,self.visit)
			elif self.PIDN[-1] == "B":
				return os.path.join(self.base_location,"SEARCH013",self.PIDN,self.visit)
			else:
				print "Study read as S013 but PIDN is missing group designation A or B"
				return None

		elif self.study == "T11":
			# T11 pidn should be PXXXX, not XXXX
			if self.PIDN[0] != "P":
				self.PIDN = "P" + self.PIDN
			return os.path.join(self.base_location,"SEARCH 023 RV405","%s.%s" % (self.study, self.PIDN),"%s.%s_%s" % (self.study, self.PIDN, self.visit) )

		elif self.study == "S398":
			# S013 pidn should not have leading P
			if self.PIDN[0] == "P":
				self.PIDN = self.PIDN[1:]

			return os.path.join(self.base_location, "SEARCH RV398", "%s_04_%s" % (self.study, self.PIDN), "%s_04_%s_%s" % (self.study, self.PIDN, self.visit) )

		elif self.study == "S018":
			print "NOT DONE YET"
			return None
		else:
			return None
		

	def find_archive_loc(self):
		if self.study and self.PIDN:
			pass
