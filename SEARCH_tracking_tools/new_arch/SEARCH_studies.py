import os
import logging


"""
To add studies, create a new class with the name and required information following the same
style as other classes. 

"""

class SEARCH_study(object):
	def __init__(self,filename):
		self.input_file = filename


		self.study = ""
		self.pidn = ""
		self.visit = ""

		self.mri_loc = ""
		self.mrs_loc = ""

		self.unzip_loc = ""

		self.T1 = []
		self.FLAIR = []
		self.TSE = []
		self.DTI2 = []
		self.DTIb0 = []
		self.fMRI = []
		self.MRS_ss = []
		self.MRS = []


		self.PatientName
		self.PatientAge
		self.PatientSex
		self.Scanner
		self.AcqDate
		self.Sequence

	def parse_filename(self,pidn_buffer=0):
		self.parser = [x for x in self.input_file[4:].split("_") if x]
		self.parsed = [self.parser[-2].zfill(pidn_buffer) , os.path.splitext(self.parser[-1])[0]]
		if self.parsed[0].startswith("P"):
			self.parsed[0] = self.parsed[0][1:]

		return self.parsed


class S010(SEARCH_study):
	def __init__(self, filename):
		# inherit the initializations in SEARCH_study class
		super(S010, self).__init__(filename)

		# Update definitions
		self.study = "S010"
		self.pidn, self.visit = self.parse_filename(pidn_buffer = 4)

	def R_location(self):
		self.mri_loc = os.path.join(R_loc,"SEARCH010","{0.study}.{0.pidn}{sep}{0.study}.{0.pidn}_{0.visit}".format(self,sep = os.sep),"mri_images")
		self.mrs_loc = os.path.join(R_loc,"SEARCH010","{0.study}.{0.pidn}{sep}{0.study}.{0.pidn}_{0.visit}".format(self,sep = os.sep),"MRS")

class S013(SEARCH_study):
	def __init__(self, filename):
		# inherit the initializations in SEARCH_study class
		super(S013, self).__init__(filename)

		# Update definitions
		self.study = "S013"
		self.pidn, self.visit = self.parse_filename(pidn_buffer = 5)

	def R_location(self):
		if self.pidn.endswith("A"):
			self.mri_loc = os.path.join(R_loc,"SEARCH013","{0.pidn}{sep}{0.visit}".format(self,sep = os.sep),"mri_images")
			self.mrs_loc = os.path.join(R_loc,"SEARCH013","{0.pidn}{sep}{0.visit}".format(self,sep = os.sep),"MRS")
		elif self.pidn.endswith("B"):
			self.mri_loc = os.path.join(R_loc,"SEARCH013","{0.pidn}{sep}{0.visit}".format(self,sep = os.sep),"mri_images")
			self.mrs_loc = os.path.join(R_loc,"SEARCH013","{0.pidn}{sep}{0.visit}".format(self,sep = os.sep),"MRS")
		else:
			logging.error("ERROR: S013 does not define substudy A or B.")
			raise Exception

		
		



## Global variables ##

known_codes = {
	"S010" : S010,
	"S013" : S013,

}

R_loc = os.path.join("R:",os.sep,"groups","valcour","SEARCH")
T1_seq = "Sag.T1W.3D"
FLAIR_seq = "Ax FLAIR"
TSE_seq = "Ax T2 TSE"
DTI2_seq = "DTI.2X2X2"
DTIb0_seq = "DTI.b0"
fMRI_seq = "Ax FFE.EPI"