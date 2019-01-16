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
Contains functions and classes needed for do_import.py to function
Steps:
	Reads all compressed files in a location
	Unzips them
	Reads the dicom headers and keeps the scans we want
	Moves the scans onto the R drive
	Opens the scans in MRIcro for QC
 
Currently implemented scanners: Ingenia, Achieva (3T Philips)
Currently implemented studies:
	SEARCH 010 (S010)
	SEARCH 013 (S013A and S013B)
	SEARCH 023 RV405 (T11)
	SEARCH 010 RV398 (S398)
	SEARCH 025

Currently detects Phantoms but does not do anything with them

To Do:
	Add Phantom code to store the files somewhere
	Add Phantom code so they do not appear as blank lines when asking for confirmation to move to R drive
	RV398 imports as S398_04_P0004, should be S398_04_0004; change either files or code to be consistent
	Move into a debug log printout instead of an excel sheet printout***


Original Author:
Kevin Chang 2018/07


Revisions:
	2018/07/31: Added functionality for when SEARCH sends rar files. Requires 7z to be in the path. Zip files are still preferable
	2018/08/01: Added code for mricro QC'ing after exporting
	2018/11/02: Added SEARCH025 processing
	2018/11/19: Added code to manage if PIDN comes with or without initial "P"
	2019/01/03: Added code to run in order of study>PIDN instead of randomly

'''



###################################################################################################################
###################################################################################################################

known_3T_scanners = ["Ingenia","Achieva"]
mricro_install_loc = os.path.join("C:",os.sep,"Program Files (x86)","MRIcro","mricro.exe")


def create_study_class(import_directory):
	compressed_files = []
	for i in os.listdir(import_directory):
		#logging.debug('this is a test')
		if i.endswith(".zip") or i.endswith(".rar"):
			compressed_files.append(i)
	compressed_files.sort()
	return compressed_files




def mricro_QC(R_drive_loc):
	# We want to QC: T1, FLAIR, TSE, rsfMRI, DTI
	#view_cmd = ""
	loc2qc_short = os.path.join(R_drive_loc, "mri_images")
	modalities = [x for x in os.listdir(loc2qc_short) if not x.startswith("MRS") and not x.endswith("b0")]
	for modality in modalities:
		loc2qc = os.path.join(loc2qc_short , modality)
		#print loc2qc
		#print os.listdir(loc2qc)
		file2qc = os.path.join(loc2qc, os.listdir(loc2qc)[0] )
		view_cmd = "\"%s\" \"%s\" " % (mricro_install_loc, file2qc)
		logging.info("   %s:%s" %(modality, view_cmd))
		print "   ", modality, ":", view_cmd
		viewer = subprocess.call(view_cmd, shell=True)



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

	seq_known = False

	if T1_pattern.search(sequence_name) and not T1_exclude.search(sequence_name):
		return ["T1","Sag.T1W.3D"]
		seq_known = True
	if TSE_pattern.search(sequence_name):
		return ["TSE","Ax T2 TSE"]
		seq_known = True
	if FLAIR_pattern.search(sequence_name):
		return ["FLAIR","Ax FLAIR"]
		seq_known = True
	if DTI2_pattern.search(sequence_name):
		return ["DTI","DTI.2X2X2"]
		seq_known = True
	if DTIb_pattern.search(sequence_name):
		return ["DTIb0","DTI.b0"]
		seq_known = True
	if fMRI_pattern.search(sequence_name):
		return ["fMRI","Ax FFE.EPI"]
		seq_known = True
	if MRS_pattern.search(sequence_name):
		return ["MRS",sequence_name]
		seq_known = True
	if seq_known == False:
		return False 

class SEARCH_importer:
	def __init__(self,name):
		self.inputpath = name
		if self.inputpath.endswith(".rar"):
			self.compress = "r"
		else:
			self.compress = "z"

		self.study = ""
		self.PIDN = ""
		self.visit = ""
		self.pdir = ""     # This is the folder that contains mri_images, MRS
		self.mri_dir = ""  # This is the mri_images location
		self.MRS_dir = ""  # This is the MRS location

		self.QA_notes = [] # keep log of possible errors here
		
		self.study_known = False
		self.proceed = True
		self.do_export = False
		
		self.MRS_count = 0
		self.MRS_screenshots = False    # set to True if MRS screenshots are present
		self.MRS_files = False          # set to True if MRS spar and sdat files are present
		self.not_images = []
		self.columns = ["Study","PIDN","Visit","AcquisitionDate","PatientAge","PatientSex","ScannerID",
						"T1","FLAIR","TSE","DTI","DTIb0","fMRI","MRS","Other"]
		self.dcmheader = pd.DataFrame([["","","","","","","",0,0,0,0,0,0,0,[]]],
									  columns=self.columns)


	def parse_study(self):
		'''
		This function reads the study code in the file name, ie S###.####.M#, and attempts to parse it into
		the known studies that are implemented in the rest of the code
		'''

		### FOR S010 and S013 ###
		if self.inputpath.startswith("S010") or self.inputpath.startswith("S013"):
			self.study_known = True
			self.study = self.inputpath[:4]
			self.other_code = filter(None, re.split('[^a-zA-Z0-9]', self.inputpath[4:]) )
			self.PIDN = self.other_code[0]
			if self.PIDN.startswith("P"):
				self.PIDN = self.PIDN[1:]
			try:
				self.visit = self.other_code[1:-1][0]
			except:
				self.visit = "NA"

		### FOR S23/T11 ###
		if self.inputpath.startswith("T11"):
			self.study_known = True
			self.other_code = self.inputpath.split("_")
			self.study = self.other_code[0]
			self.PIDN = self.other_code[1]
			try:
				self.visit = self.other_code[2][:-4]
			except:
				self.visit = "NA"

		### FOR S010 RV398 ###
		if self.inputpath.startswith("S398"):
			self.study_known = True
			self.study = self.inputpath[:4]
			self.other_code = self.inputpath[8:].split("_")
			self.PIDN = self.other_code[0]
			try:
				self.visit = self.other_code[1][:-4]
			except:
				self.visit = "NA"

		### FOR S025 ###
		if self.inputpath.startswith("S025"):
			self.study_known = True
			self.other_code = self.inputpath.split("_")
			self.study = self.other_code[0]
			self.PIDN = self.other_code[1][1:]
			try:
				self.visit = self.other_code[2][:-4]
			except:
				self.visit = "NA"

		### FOR PHANTOMS ###
		if self.inputpath.startswith("Phantom"):
			self.study_known = True
			print "Phantom Scan detected: ignoring"
			logging.info("Phantom Scan detected: %s" % self.inputpath)
			self.proceed = False

		### ELSE WE DO NOT KNOW STUDY ###
		if self.study_known == False:
			print "%s does not match any currently implemented SEARCH study code." % self.inputpath
			logging.info("%s does not match any currently implemented SEARCH study code." % self.inputpath)
			self.proceed == False
		
		### IF WE KNOW STUDY, MOVE FORWARDS ###
		if self.proceed == True:
			print "STUDY: ",self.study
			print "PIDN:  ",self.PIDN
			print "Visit: ",self.visit
			logging.info("Study: %s\nPIDN: %s\nVisit: %s" %(self.study, self.PIDN, self.visit))
			

		if self.visit == "NA":
			self.QA_notes.append("Visit code not read correctly; ")
			logging.info("Visit code could not be read at %s" % self.inputpath)
		
	def unzip(self):
		if self.study and self.PIDN and self.visit:
			self.pdir = os.path.join("%s.P%s" % (self.study,self.PIDN) , "%s.P%s_%s" % (self.study,self.PIDN,self.visit) )
			self.mri_dir = os.path.join(self.pdir, "mri_images")
			self.MRS_dir = os.path.join(self.pdir, "MRS")
			
			if os.path.isdir(self.pdir):
				print "%s already exists!" % self.pdir
				logging.warning("%s already exists!" % self.pdir)
				self.proceed = False
			else:
				print "Extracting %s.P%s_%s to %s" % (self.study,self.PIDN,self.visit,self.pdir)
				logging.info("Extracting %s.P%s_%s to %s" % (self.study,self.PIDN,self.visit,self.pdir))
				os.makedirs( self.pdir )
				os.makedirs( self.mri_dir )
				os.makedirs( self.MRS_dir )
			if self.compress == "r":
				# If .rar compressed
				rar_cmd = "7z x %s -o%s" % (self.inputpath, self.pdir)
				run_unrar = subprocess.call(rar_cmd, stdout=subprocess.PIPE,stderr=subprocess.PIPE )

			else:
				# If .zip compressed
				zip_ref = ZipFile(self.inputpath, 'r')
				zip_ref.extractall(self.pdir)
				zip_ref.close()

	def dicom_read(self):
		if self.pdir and self.proceed:
			for root,dirs,files in os.walk(self.pdir):
				#print root,dirs,files
				
				if files and re.search("DICOM",root,re.IGNORECASE):
					#print root,dirs,files
					for dcm in files:
						try:
							# Do header info strip here
							self.dicom_header_import(root, dcm)
							# result is a filled out table
							if self.dcmheader.loc[0,"MRS"] > 1:
								self.MRS_screenshots = True
							
							pass
						except Exception as e:
							raise e
							print "ERROR in dicomread at %s" % dcm
							
							
				for file_test in files:
					if re.search("spar""|""sdat", file_test, re.IGNORECASE):
						self.MRS_files = True
						self.MRS_count += 1
						for mrsfile in files:
							if re.search("spar""|""sdat", mrsfile, re.IGNORECASE):
								mrs_filepath = os.path.join(root,mrsfile)
								shutil.copy( mrs_filepath, self.MRS_dir )
								del mrs_filepath
			print "NOT IMAGES: ", self.not_images
			print ""
			print "%s MRS files found, saving to %s" % (self.MRS_count, self.MRS_dir)
			if self.MRS_screenshots and not self.MRS_files:
				print "WARNING: MRS screenshots present but no MRS files found."
					
		
			print self.dcmheader.iloc[:,7:-1]
			print ""
			print "%s Other unprocessed scans" % len(self.dcmheader.Other.values[0])
		
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
			logging.info("PatientName read as: %s" % dicom_name)
		except:
			dicom_name = "ERROR"
		logging.info("PatientName read as: %s" % dicom_name)
		try:
			pAcqDate = datetime.strftime(datetime.strptime(header.StudyDate,"%Y%m%d"),"%Y-%m-%d")
		except:
			pAcqDate = "N/A"
		logging.info("Acquisition Date read as: %s" % pAcqDate)
		try:
			pSex = header.PatientSex
		except:
			pSex = "N/A"
		logging.info("Patient sex read as: %s" % pSex)
		try:
			pAge = header.PatientAge
		except:
			pAge = "N/A"
		logging.info("Patient age read as: %s" % pAge)
		try:
			pScanner = header.ManufacturerModelName
		except:
			pScanner = "N/A"
		logging.info("Scanner read as: %s" % pScanner)
		try:
			pSeq = header.SeriesDescription
		except:
			pSeq = "N/A"
		logging.info("Sequence read as: %s" % pSeq)
		
		# read dicom_name to see if matches study, PIDN, visit
		self.match = True
		if re.search(self.study,dicom_name):
			self.dcmheader.loc[0,"Study"] = self.study
		else:
			self.dcmheader.loc[0,"Study"] = "CHECK HEADER"
			self.QA_notes.append("Study mismatch in dicom header; ")
			self.match = False
			logging.warning("Check dicom header study: %s not found in %s" %(self.study, dicom_name))
		if re.search(self.PIDN,dicom_name):
			self.dcmheader.loc[0,"PIDN"] = self.PIDN
		else:
			self.dcmheader.loc[0,"PIDN"] = "CHECK HEADER"
			self.QA_notes.append("PIDN mismatch in dicom header; ")
			self.match = False
			logging.warning("Check dicom header name: %s not found in %s" %(self.PIDN, dicom_name))
		if re.search(self.visit,dicom_name):
			self.dcmheader.loc[0,"Visit"] = self.visit
		else:
			self.dcmheader.loc[0,"Visit"] = "CHECK HEADER"
			self.QA_notes.append("Visit mismatch in dicom header; ")
			self.match = False
			logging.warning("Check dicom header visit: %s not found in %s" %(self.visit, dicom_name))

		if self.dcmheader.loc[0,"AcquisitionDate"] == "":
			self.dcmheader.loc[0,"AcquisitionDate"] = pAcqDate
		elif self.dcmheader.loc[0,"AcquisitionDate"] != pAcqDate:
			self.QA_notes.append("AcqDate mismatch in dicom header; ")
			self.match = False


		if self.dcmheader.loc[0,"PatientAge"] == "":
			self.dcmheader.loc[0,"PatientAge"] = pAge
		elif self.dcmheader.loc[0,"PatientAge"] != pAge:
			self.QA_notes.append("Age mismatch in dicom header; ")
			self.match = False


		if self.dcmheader.loc[0,"PatientSex"] == "":
			self.dcmheader.loc[0,"PatientSex"] = pSex
		elif self.dcmheader.loc[0,"PatientSex"] != pSex:
			self.QA_notes.append("Sex mismatch in dicom header; ")
			self.match = False


		if self.dcmheader.loc[0,"ScannerID"] == "":
			self.dcmheader.loc[0,"ScannerID"] = pScanner
		elif self.dcmheader.loc[0,"ScannerID"] != pScanner:
			self.QA_notes.append("Scanner mismatch in dicom header; ")
			self.match = False

		if self.match == False:
			print "WARNING: DICOM HEADER INCONSISTENCY AT %s" % dcmfile
			logging.warning("Please check the dicom headers for inconsistencies for %s" % dcmfile)

		
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
			#print "WARNING: %s is not an image" % dcmfile
			self.not_images.append(dcmfile)
		elif pScanner not in known_3T_scanners:
			#print "WARNING: %s/%s is scanned on %s, automatic processing not implemented!" % (root,dcmfile,pScanner)
			logging.warning("%s/%s is scanned on %s, automatic processing not implemented!" % (root,dcmfile,pScanner))
			self.QA_notes.append("Not auto-processed due to scanner name; ")
		else:
			#print "No image at %s/%s" % (root,dcmfile)
			pass

		
		
		
		# reset variables
		del header, dicom_name, pAcqDate,pSex,pAge,pScanner,pSeq, dicom_loc

	def R_export(self):
		#print "test"
		R_drive = os.path.join("R:\\groups\\valcour\\SEARCH")
		#del self.R_exportloc,self.export_success
		self.export_success = False
		if self.study and self.PIDN and self.visit:



			### S010 Export Location ###
			if self.study == "S010":
				self.R_exportloc = os.path.join(R_drive, "SEARCH010","%s.P%s" % (self.study,self.PIDN),"%s.P%s_%s" % (self.study,self.PIDN,self.visit))
			### S013 Export Location ###
			if self.study == "S013":
				if self.PIDN.endswith("B"):
					self.R_exportloc = os.path.join(R_drive, "SEARCH013","%s" % (self.PIDN),"%s" % (self.visit))
				elif self.PIDN.endswith("A"):
					self.R_exportloc = os.path.join(R_drive, "SEARCH013", "Controls", "%s" % (self.PIDN),"%s" % (self.visit))
			### T11/S23 Export Location ###
			if self.study == "T11":
				self.R_exportloc = os.path.join(R_drive, "SEARCH023 RV405","%s.P%s" % (self.study,self.PIDN),"%s.P%s_%s" % (self.study,self.PIDN,self.visit))

			### RV398 Export Location ###
			if self.study == "S398":
				self.R_exportloc = os.path.join(R_drive, "SEARCH RV398","%s_04_%s" % (self.study,self.PIDN),"%s_04_%s_%s" % (self.study,self.PIDN,self.visit))            

			### S025 Export Location ###
			if self.study == "S025":
				self.R_exportloc = os.path.join(R_drive, "SEARCH025","%s_P%s" % (self.study,self.PIDN),"%s_P%s_%s" % (self.study,self.PIDN,self.visit))        

			### Do Export Here ###
			if os.path.isdir(self.R_exportloc):
				print "EXPORT ERROR: %s already exists." % (self.R_exportloc)
				self.export_success = False
			else:
				os.makedirs(self.R_exportloc)
				print "EXPORTING %s %s %s to %s" % (self.study,self.PIDN,self.visit,self.R_exportloc)
				print ""
				shutil.move(self.mri_dir,self.R_exportloc)
				if self.MRS_files:
					shutil.move(self.MRS_dir,self.R_exportloc)
				self.export_success = True
				## return location for QCing ##
				# print QC cmd probably not working
				### Do QC of scans ###
				print "QC'ing %s %s %s" % (self.study,self.PIDN,self.visit)
				mricro_QC(self.R_exportloc)



				#print "QC cmd: cd %s && \"%s\" %s && %\"%s\" %s && \"%s\" %s" % (os.path.join(self.R_exportloc,"mri_images"),
			#												 mricro_location, "Sag.T1W.3D/*.dcm",
			#												 mricro_location, "Ax\" \"FLAIR/*.dcm",
			#												 mricro_location, "Ax\" \"T2\" \"TSE/*.dcm")


def create_output_logs(holder, zipped_ftp_import_location):
	output_columns = ["PIDN","Visit","MRI Date","Scanner","MR Received","T1","FLAIR","TSE","DTI","DTIb0","rsfMRI","MRS Rec","MRS ss","MRS sent","MRS quant.","Comments"]
	S398_output_log = pd.DataFrame(columns=output_columns)

	output_columns2 = output_columns
	output_columns2.insert(3,"Age")
	output_columns2.insert(4,"Gender")
	S013_output_log = pd.DataFrame(columns=output_columns2)
	S010_output_log = S013_output_log

	output_columns3 = output_columns
	output_columns3.insert(1,"S010 PIDN")
	S023_output_log = pd.DataFrame(columns=output_columns3)
	S025_output_log = S023_output_log

	other_log = pd.DataFrame()

	# columns are: ["Study","PIDN","Visit","AcquisitionDate","PatientAge","PatientSex","ScannerID","T1","FLAIR","TSE","DTI","DTIb0","fMRI","MRS","Other"]

	for i in holder:
		if holder[i].study=="S010":
			holder[i].entry = pd.DataFrame(columns=S010_output_log.columns)
			holder[i].entry.loc[0,"PIDN"] = "P"+holder[i].PIDN
			holder[i].entry.loc[0, "Visit"] = holder[i].visit
			holder[i].entry.loc[0, "MRI Date"] = holder[i].dcmheader.iloc[0]["AcquisitionDate"]
			holder[i].entry.loc[0,"Age"] = holder[i].dcmheader.iloc[0]["PatientAge"]
			holder[i].entry.loc[0,"Gender"] = holder[i].dcmheader.iloc[0]["PatientSex"]
			holder[i].entry.loc[0, "Scanner"] = holder[i].dcmheader.iloc[0]["ScannerID"]
			holder[i].entry.loc[0, "MR Received"] = 1
			holder[i].entry.loc[0, "T1"] = holder[i].dcmheader.iloc[0]["T1"]
			holder[i].entry.loc[0, "FLAIR"] = holder[i].dcmheader.iloc[0]["FLAIR"]
			holder[i].entry.loc[0, "TSE"] = holder[i].dcmheader.iloc[0]["TSE"]
			holder[i].entry.loc[0, "DTI"] = holder[i].dcmheader.iloc[0]["DTI"]
			holder[i].entry.loc[0, "DTIb0"] = holder[i].dcmheader.iloc[0]["DTIb0"]
			holder[i].entry.loc[0, "rsfMRI"] = holder[i].dcmheader.iloc[0]["fMRI"]
			holder[i].entry.loc[0, "MRS Rec"] = int(holder[i].MRS_files)
			holder[i].entry.loc[0, "MRS ss"] = holder[i].dcmheader.iloc[0]["MRS"]
			holder[i].entry.loc[0, "MRS sent"] = 0
			holder[i].entry.loc[0, "MRS quant."] = 0
			holder[i].entry.loc[0, "Comments"] = list(set(holder[i].QA_notes))

			S010_output_log = S010_output_log.append(holder[i].entry)

		if holder[i].study=="S013":
			holder[i].entry = pd.DataFrame(columns=S013_output_log.columns)
			holder[i].entry.loc[0,"PIDN"] = holder[i].PIDN
			holder[i].entry.loc[0, "Visit"] = holder[i].visit
			holder[i].entry.loc[0, "MRI Date"] = holder[i].dcmheader.iloc[0]["AcquisitionDate"]
			holder[i].entry.loc[0,"Age"] = holder[i].dcmheader.iloc[0]["PatientAge"]
			holder[i].entry.loc[0,"Gender"] = holder[i].dcmheader.iloc[0]["PatientSex"]
			holder[i].entry.loc[0, "Scanner"] = holder[i].dcmheader.iloc[0]["ScannerID"]
			holder[i].entry.loc[0, "MR Received"] = 1
			holder[i].entry.loc[0, "T1"] = holder[i].dcmheader.iloc[0]["T1"]
			holder[i].entry.loc[0, "FLAIR"] = holder[i].dcmheader.iloc[0]["FLAIR"]
			holder[i].entry.loc[0, "TSE"] = holder[i].dcmheader.iloc[0]["TSE"]
			holder[i].entry.loc[0, "DTI"] = holder[i].dcmheader.iloc[0]["DTI"]
			holder[i].entry.loc[0, "DTIb0"] = holder[i].dcmheader.iloc[0]["DTIb0"]
			holder[i].entry.loc[0, "rsfMRI"] = holder[i].dcmheader.iloc[0]["fMRI"]
			holder[i].entry.loc[0, "MRS Rec"] = int(holder[i].MRS_files)
			holder[i].entry.loc[0, "MRS ss"] = holder[i].MRS_count
			holder[i].entry.loc[0, "MRS sent"] = 0
			holder[i].entry.loc[0, "MRS quant."] = 0
			holder[i].entry.loc[0, "Comments"] = list(set(holder[i].QA_notes))

			S013_output_log = S013_output_log.append(holder[i].entry)


		if holder[i].study=="S398":
			holder[i].entry = pd.DataFrame(columns=S398_output_log.columns)
			holder[i].entry.loc[0,"PIDN"] = holder[i].PIDN
			holder[i].entry.loc[0, "Visit"] = holder[i].visit
			holder[i].entry.loc[0, "MRI Date"] = holder[i].dcmheader.iloc[0]["AcquisitionDate"]
			holder[i].entry.loc[0, "Scanner"] = holder[i].dcmheader.iloc[0]["ScannerID"]
			holder[i].entry.loc[0, "MR Received"] = 1
			holder[i].entry.loc[0, "T1"] = holder[i].dcmheader.iloc[0]["T1"]
			holder[i].entry.loc[0, "FLAIR"] = holder[i].dcmheader.iloc[0]["FLAIR"]
			holder[i].entry.loc[0, "TSE"] = holder[i].dcmheader.iloc[0]["TSE"]
			holder[i].entry.loc[0, "DTI"] = holder[i].dcmheader.iloc[0]["DTI"]
			holder[i].entry.loc[0, "DTIb0"] = holder[i].dcmheader.iloc[0]["DTIb0"]
			holder[i].entry.loc[0, "rsfMRI"] = holder[i].dcmheader.iloc[0]["fMRI"]
			holder[i].entry.loc[0, "MRS Rec"] = int(holder[i].MRS_files)
			holder[i].entry.loc[0, "MRS ss"] = holder[i].MRS_count
			holder[i].entry.loc[0, "MRS sent"] = 0
			holder[i].entry.loc[0, "MRS quant."] = 0
			holder[i].entry.loc[0, "Comments"] = list(set(holder[i].QA_notes))

			S398_output_log = S398_output_log.append(holder[i].entry)


		if holder[i].study=="T11":
			holder[i].entry = pd.DataFrame(columns=S023_output_log.columns)
			holder[i].entry.loc[0,"PIDN"] = holder[i].PIDN
			holder[i].entry.loc[0, "Visit"] = holder[i].visit
			holder[i].entry.loc[0, "MRI Date"] = holder[i].dcmheader.iloc[0]["AcquisitionDate"]
			holder[i].entry.loc[0, "Scanner"] = holder[i].dcmheader.iloc[0]["ScannerID"]
			holder[i].entry.loc[0, "MR Received"] = 1
			holder[i].entry.loc[0, "T1"] = holder[i].dcmheader.iloc[0]["T1"]
			holder[i].entry.loc[0, "FLAIR"] = holder[i].dcmheader.iloc[0]["FLAIR"]
			holder[i].entry.loc[0, "TSE"] = holder[i].dcmheader.iloc[0]["TSE"]
			holder[i].entry.loc[0, "DTI"] = holder[i].dcmheader.iloc[0]["DTI"]
			holder[i].entry.loc[0, "DTIb0"] = holder[i].dcmheader.iloc[0]["DTIb0"]
			holder[i].entry.loc[0, "rsfMRI"] = holder[i].dcmheader.iloc[0]["fMRI"]
			holder[i].entry.loc[0, "MRS Rec"] = int(holder[i].MRS_files)
			holder[i].entry.loc[0, "MRS ss"] = holder[i].MRS_count
			holder[i].entry.loc[0, "MRS sent"] = 0
			holder[i].entry.loc[0, "MRS quant."] = 0
			holder[i].entry.loc[0, "Comments"] = list(set(holder[i].QA_notes))

			S023_output_log = S023_output_log.append(holder[i].entry)

		if holder[i].study=="S025":
			holder[i].entry = pd.DataFrame(columns=S025_output_log.columns)
			holder[i].entry.loc[0,"PIDN"] = holder[i].PIDN
			holder[i].entry.loc[0, "Visit"] = holder[i].visit
			holder[i].entry.loc[0, "MRI Date"] = holder[i].dcmheader.iloc[0]["AcquisitionDate"]
			holder[i].entry.loc[0, "Scanner"] = holder[i].dcmheader.iloc[0]["ScannerID"]
			holder[i].entry.loc[0, "MR Received"] = 1
			holder[i].entry.loc[0, "T1"] = holder[i].dcmheader.iloc[0]["T1"]
			holder[i].entry.loc[0, "FLAIR"] = holder[i].dcmheader.iloc[0]["FLAIR"]
			holder[i].entry.loc[0, "TSE"] = holder[i].dcmheader.iloc[0]["TSE"]
			holder[i].entry.loc[0, "DTI"] = holder[i].dcmheader.iloc[0]["DTI"]
			holder[i].entry.loc[0, "DTIb0"] = holder[i].dcmheader.iloc[0]["DTIb0"]
			holder[i].entry.loc[0, "rsfMRI"] = holder[i].dcmheader.iloc[0]["fMRI"]
			holder[i].entry.loc[0, "MRS Rec"] = int(holder[i].MRS_files)
			holder[i].entry.loc[0, "MRS ss"] = holder[i].MRS_count
			holder[i].entry.loc[0, "MRS sent"] = 0
			holder[i].entry.loc[0, "MRS quant."] = 0
			holder[i].entry.loc[0, "Comments"] = list(set(holder[i].QA_notes))

			S025_output_log = S025_output_log.append(holder[i].entry)


		other_log = pd.concat([other_log,holder[i].dcmheader])


	# convert to excel

	now = datetime.now()
	date = now.strftime("%Y%m%d")

	output_loc = os.path.join(zipped_ftp_import_location,"BK_import_log_%s.xlsx" % date)
	output_continue = False
	while output_continue == False:
		counter = 1
		if os.path.isfile(output_loc):
			output_loc = "%s_%s" % (output_loc, counter)
			counter += 1
		else:
			output_continue = True

	writer = pd.ExcelWriter(output_loc , engine = 'xlsxwriter')

	S010_output_log.to_excel(writer,sheet_name = "S010", index=False)
	S013_output_log.to_excel(writer,sheet_name = "S013", index=False)
	S398_output_log.to_excel(writer,sheet_name = "S010 RV398", index=False)
	S023_output_log.to_excel(writer,sheet_name = "S023 RV405", index=False)
	S025_output_log.to_excel(writer,sheet_name = "S025", index=False)
	other_log.to_excel(writer,sheet_name = "Full_script_output")
	writer.save()






					
def run_import_steps(path):
	print path
	os.chdir(path)
	os.listdir(os.getcwd())
	holder = {name: SEARCH_importer(name=name) for name in create_study_class(path)}
	holder_keys = holder.keys()
	holder_keys.sort()
	print "=========================="
	print "   Local Processing...."
	print "=========================="
		
	## Do unzipping and processing ##
	try:
		for i in holder_keys:
			print "-----------------------"
			print i
			print "-----------------------"
			holder[i].parse_study()
			if holder[i].proceed:
				holder[i].unzip()
				holder[i].dicom_read()
		print ""
		print "Local Processing Done"
		print ""
	except Exception as e:
		raise e
	
	return holder
	
def run_archive_steps(holder, path):
	## do archiving ##
	print "=========================="
	print "   R Drive Exporting...."
	print "=========================="
	os.chdir(path)
	counter = 0
	counter_ = 0
	holder_keys = holder.keys()
	holder_keys.sort()

	for i in holder_keys:
		if holder[i].proceed:
			holder[i].do_export = raw_input(
				"Export %s %s %s to R drive image archive? (y/n): " % (holder[i].study,holder[i].PIDN,holder[i].visit ))
			pause1 = 0
			while pause1 == 0:
				if holder[i].do_export == "y":
				#holder[i].do_export == True
				#print "    to export"
					pass
					pause1 = 1
				elif holder[i].do_export == "n":
				#holder[i].do_export == False
					print "    %s %s %s will not be exported" % (holder[i].study,holder[i].PIDN,holder[i].visit )
					pause1 = 1
				else:
					holder[i].do_export = raw_input("     Please enter (y/n): ")
		else:
			print "Export not proceeding for %s %s %s" % (holder[i].study,holder[i].PIDN,holder[i].visit )
	print ""
	for i in holder_keys:
		if holder[i].do_export == "y":
			print "-----------------------"
			print i
			print "-----------------------"
			try:
				holder[i].R_export()
				counter += 1
			except:
				print "Export failed for %s %s %s" % (holder[i].study,holder[i].PIDN,holder[i].visit )
				counter_ += 1

	print ""
	print "=========================="
	if counter > 0:
		print "R Drive Archive Export Done"
		print "%s Subjects were exported" % counter
		if counter_ > 0:
			print "%s Subjects failed export - rerun from top" % counter_
	elif counter_ > 0:
		print "%s Subjects failed export - rerun from top" % counter_
	else:
		print "No Subjects Exported"
	print "=========================="


################################
