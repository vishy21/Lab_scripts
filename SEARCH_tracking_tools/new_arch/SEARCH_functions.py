import SEARCH_studies as study_
import logging
import os
from zipfile import ZipFile
import pydicom
import re

def do_import(directory):
	## Runs through import steps for each file in directory that is compressed ##
	directory_files = os.listdir(directory)
	study_class_batch = []
	logging.info("="*50 + "\nBeginning import of compressed files.\n"+"="*50)
	for file in directory_files:
		study_class = import_initialize(file)

		# If successfully created study class, proceed
		if study_class:
			# Build R drive path
			study_class.R_location()

			# If path already exists on R drive, then do not proceed so we don't override existing data.
			if os.path.isdir(study_class.mri_loc):
				logging.error("ERROR: %s already exists. Ending processing" % study_class.mri_loc)
				del study_class
			# Otherwise, we are free to proceed.
			else:
				# Add file to a list
				study_class_batch += [study_class]
				do_unzip(study_class)
				find_images(study_class)
				# after finding all images, we should then check if the pt info is matching for all scans

				# unzip the file
				# find the dicoms
				# find the images we care about
				# find the MRS files
				# collect all and prepare to move to R drive



	#files2process = [study_ for study_ in [import_initialize(file) for file in directory] if study_]
	logging.info("\n%s study files were successfully read." % (len(study_class_batch)) )



def import_initialize(filename):
	# Initializes the import process by reading file names
	# Returns created study class with Study, PIDN, and visit
	logging.info("\n"+"-"*50 + "\n%s\n" % (filename) + "-"*50 )
	if filename.endswith(".zip") or filename.endswith(".rar"):
		known = False
		for known_code in study_.known_codes.keys():
			if filename.startswith(known_code):
				created_class = study_.known_codes[known_code](filename)
				logging.info("STUDY:\t{0.study}\nPIDN:\t{0.pidn}\nVISIT:\t{0.visit}".format(created_class))
				return created_class
				known = True

		if known == False:
			logging.error("ERROR: Unknown Study - skipping...")

	else:
		logging.warning("File is not compressed - skipping...")

def do_unzip(study):
	pass
	try:
		if study.mri_loc:
			pass

	except:
		logging.error("Missing information.")
	# check if we have the needed information:
	if study.mri_loc and study.study and study.pidn and study.visit:
		pass
		if study.input_file.endswith(".zip"):
			study.extract_dir = study.input_file[:-4]
			if os.path.isdir(study.extract_dir) == False:
				os.makedirs(study.extract_dir)
				logging.info("Creating unzip directory at %s" % study.extract_dir)
				unzipper = ZipFile(study.input_file, "r")
				unzipper.extractall(study.extract_dir)
				unzipper.close()
				logging.info("Extraction complete.")
			else:
				logging.error("%s already exists!" % study.extract_dir)

		elif study.input_file.endswith(".rar"):
			logging.error("RAR uncompressing not yet implemented.")

		# study.filename is input zip file

	else:
		logging.error("Missing information. Skipping processing")

def find_images(study):
	pass
	for root,dirs,files in os.walk(study.extract_dir):
		if files and re.search("DICOM",root,re.IGNORECASE):
			dicoms = []
			not_dicoms = []
			for dcm in files:
				try:
					# try to read dicoms
					read_dicom_header(root,dcm,study)
					###
				except:
					# if not dicom, read fails
					pass



		for mrs_ in files:
			if mrs_.endswith(".spar") or mrs_.endswith(".sdat"):
				mrs_loc = os.path.join(root, mrs_)
				self.MRS += [mrs_loc]


	# Print out what scan sequences we have located. Should have at least 1 of each, with 2 MRS screenshots
	logging.info("%s T1, %s FLAIR, %s TSE, %s DTI.2x2x2, %s DTI.b0, %s fMRI, %s MRS screenshots found" % (
		len(study.T1), len(study.FLAIR), len(study.TSE), len(study.DTI2), len(study.DTIb0), len(study.fMRI), len(study.MRS_ss), ))
	logging.info("%s MRS files found" % len(study.MRS))

	# If we find the screenshots but not the actual MRS files, print out message:
	if len(study.MRS) == 0 and len(study.MRS_ss) > 0:
		logging.warning("WARNING! MRS screenshots are found but no MRS files!")
	# read through study.extract_dir to find where dicoms and MRS are

def read_dicom_header(root,dcm,study):
	pass
	ds = pydicom.dcmread(os.path.join(root,dcm))
	# get header data
	if "PixelData" in ds:
		header_info = {}
		try:
			header_info["Name"] = ds.PatientName
		except:
			pass
		try:
			header_info["Sex"] = ds.PatientSex
		except:
			pass
		try:
			header_info["Age"] = ds.PatientAge
		except:
			pass
		try:
			header_info["Date"] = ds.StudyDate
		except:
			pass
		try:
			header_info["Scanner"] = ds.ManufacturerModelName
		except:
			pass
		try:
			header_info["Sequence"] = ds.SeriesDescription
		except:
			pass
	# if pixeldata and known scanner, then read and prep for import
		if header_info["Sequence"] == study_.T1_seq:
			header_info["path"] == os.path.join(root,dcm)
			study.T1 += [header_info]
		elif header_info["Sequence"] == study_.FLAIR_seq:
			header_info["path"] == os.path.join(root,dcm)
			study.FLAIR += [header_info]
		elif header_info["Sequence"] == study_.TSE_seq:
			header_info["path"] == os.path.join(root,dcm)
			study.TSE += [header_info]
		elif header_info["Sequence"] == study_.DTI2_seq:
			header_info["path"] == os.path.join(root,dcm)
			study.DTI2 += [header_info]
		elif header_info["Sequence"] == study_.DTIb0_seq:
			header_info["path"] == os.path.join(root,dcm)
			study.DTIb0 += [header_info]
		elif header_info["Sequence"] == study_.fMRI_seq:
			header_info["path"] == os.path.join(root,dcm)
			study.fMRI += [header_info]
		elif header_info["Sequence"].startwith("MRS"):
			header_info["path"] == os.path.join(root,dcm)
			study.MRS_ss += [header_info]
		




