#!/usr/bin/python
import os
import dipy
import nibabel as nib
import subprocess

from dipy.io import read_bvals_bvecs
from dipy.core.gradients import gradient_table


############################
# Creates a b0 image from the 2X2X2 img in case one doesn't already exist
# i.e.: from the S018 Achieva scanners
# Run from patient folder (i.e.: PIDN/DATE/PIDN/)
# should have within this folder DTI.2X2X2
# Creates a DTI.b0 folder and outputs the created b0 scan there
############################

if os.path.exists("DTI.b0"):
	print "DTI.b0 directory already exists!"
else:
	os.mkdir("DTI.b0")
	pt_path = os.getcwd()
	dir_contents = os.listdir(pt_path)
	dti_path1 = "DTI.2X2X2"
	dti_path2 = "DTI.2x2x2"

	if dti_path1 in dir_contents:
		dti_path = dti_path1
	elif dti_path2 in dir_contents:
		dti_path = dti_path2
	else:
		print "no DTI directory found"
	
	os.chdir("%s/%s" %(pt_path,dti_path) )

	lst = os.listdir(os.getcwd())

	# if  there are no .nii files but there are .dcm files:
	if len([q for q in lst if q.endswith(".nii")]) == 0 and len([p for p in lst if p.endswith(".dcm")]) > 0:
		# convert dcm to nii first
		dcm2nii = "dcm2nii -a n -d n -e n -g n -i n -p n -f y -v n"
		cmd = "%s %s/%s" %(dcm2nii, pt_path, dti_path)

		try:
			proc = subprocess.Popen( cmd, shell = True,
			                         stdout=subprocess.PIPE,
			                         stderr=subprocess.PIPE )
		except:
			print "dcm2nii error"

	# if there are already .nii files:
	if len([r for r in lst if r.endswith(".nii")]) > 0:

		for i in lst:
			if i.endswith(".bval"):
				bvals = i
			if i.endswith(".bvec"):
				bvecs = i
			if i.endswith(".nii") and i.startswith("x"):
				dti_file = i

		img = nib.load(dti_file)
		data = img.get_data()
		gtab = gradient_table(bvals, bvecs)

		B0 = data[:, :, :, gtab.b0s_mask]

		os.chdir("%s/DTI.b0" %pt_path)

		nib.save(nib.Nifti1Image(B0, img.affine), 'b0_from_2x2x2.nii')



