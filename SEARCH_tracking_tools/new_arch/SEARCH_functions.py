import SEARCH_studies as study
import logging
import os
from zipfile import ZipFile

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
				read_dicom_header(study_class)

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
		for known_code in study.known_codes.keys():
			if filename.startswith(known_code):
				created_class = study.known_codes[known_code](filename)
				logging.info("STUDY:\t{0.study}\nPIDN:\t{0.pidn}\nVISIT:\t{0.visit}".format(created_class))
				return created_class
				known = True

		if known == False:
			logging.error("ERROR: Unknown Study - skipping...")

	else:
		logging.warning("File is not compressed - skipping...")

def do_unzip(self):
	pass
	try:
		if self.mri_loc:
			pass

	except:
		logging.error("Missing information.")
	# check if we have the needed information:
	if self.mri_loc and self.study and self.pidn and self.visit:
		pass
		if self.input_file.endswith(".zip"):
			self.extract_dir = self.input_file[:-4]
			os.makedirs(self.extract_dir)
			logging.info("Creating unzip directory at %s" % self.extract_dir)
			unzipper = ZipFile(self.input_file, "r")
			unzipper.extractall(self.extract_dir)
			unzipper.close()
			logging.info("Extraction complete.")

		elif self.input_file.endswith(".rar"):
			logging.error("RAR uncompressing not yet implemented.")

		# self.filename is input zip file

	else:
		logging.error("Missing information. Skipping processing")

def find_images(self):
	pass

def read_dicom_header(self):
	pass

