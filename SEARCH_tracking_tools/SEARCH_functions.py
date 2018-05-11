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

##################################

zipped_ftp_import_location = os.path.join("C:\Users\sf287610\Desktop\Compressed_Scans","test0")
mricro_location= os.path.join("C:\Program Files (x86)\MRIcro\mricro.exe")


###################################
def create_study_class(import_directory):
    zip_files = []
    for i in os.listdir(import_directory):
        if i.endswith(".zip"):
            zip_files.append(i)
    return zip_files

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

class SEARCH_study:
    def __init__(self,name):
        self.inputpath = name
        self.study = ""
        self.PIDN = ""
        self.visit = ""
        self.pdir = ""     # This is the folder that contains mri_images, MRS
        self.mri_dir = ""  # This is the mri_images location
        self.MRS_dir = ""  # This is the MRS location        
        
        self.proceed = True
        self.do_export = False
        
        self.MRS_count = 0
        self.MRS_screenshots = False    # set to True if MRS screenshots are present
        self.MRS_files = False          # set to True if MRS spar and sdat files are present
        self.columns = ["Study","PIDN","Visit","AcquisitionDate","PatientAge","PatientSex","ScannerID",
                        "T1","FLAIR","TSE","DTI","DTIb0","fMRI","MRS","Other"]
        self.dcmheader = pd.DataFrame([["","","","","","","",0,0,0,0,0,0,0,[]]],
                                      columns=self.columns)        
    def parse_study(self):
        #print study_n
        if self.inputpath.startswith("S010") or self.inputpath.startswith("S013"):
            self.study = self.inputpath[:4]
            self.other_code = filter(None, re.split('[^a-zA-Z0-9]', self.inputpath[4:]) )
            self.PIDN = self.other_code[0]
            try:
                self.visit = self.other_code[1:-1][0]
            except:
                self.visit = "NA"
        if self.inputpath.startswith("T11"):
            self.other_code = self.inputpath.split("_")
            self.study = self.other_code[0]
            self.PIDN = self.other_code[1]
            try:
                self.visit = self.other_code[2][:-4]
            except:
                self.visit = "NA"
        if self.inputpath.startswith("S398"):
            self.study = self.inputpath[:4]
            self.other_code = self.inputpath[8:].split("_")
            self.PIDN = self.other_code[0]
            try:
                self.visit = self.other_code[1]
            except:
                self.visit = "NA"
        if self.inputpath.startswith("Phantom"):
            print "Phantom Scan detected: ignoring"
            self.proceed = False
        else:
            print "STUDY: ",self.study
            print "PIDN:  ",self.PIDN
            print "Visit: ",self.visit
        
    def unzip(self):
        if self.study and self.PIDN and self.visit:
            self.pdir = os.path.join("%s.P%s" % (self.study,self.PIDN) , "%s.P%s_%s" % (self.study,self.PIDN,self.visit) )
            self.mri_dir = os.path.join(self.pdir, "mri_images")
            self.MRS_dir = os.path.join(self.pdir, "MRS")
            
            if os.path.isdir(self.pdir):
                print "%s already exists!" % self.pdir
                self.proceed = False
            else:
                print "Extracting %s.P%s_%s to %s" % (self.study,self.PIDN,self.visit,self.pdir)
                os.makedirs( self.pdir )
                os.makedirs( self.mri_dir )
                os.makedirs( self.MRS_dir )
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
            print "%s MRS files found, saving to %s" % (self.MRS_count, self.MRS_dir)
            if self.MRS_screenshots and not self.MRS_files:
                print "WARNING: MRS screenshots present but no MRS files found."
                    
        
        print self.dcmheader.iloc[:,7:-1]
        print "%s Other unprocessed scans" % len(self.dcmheader.Other.values[0])
        #extracted = os.listdir(self.pdir)
        #dicom_pattern = re.compile("DICOM")
        
    def dicom_header_import(self,root,dcmfile):
        dicom_loc = os.path.join(root, dcmfile)
        header = dicom.read_file(dicom_loc)
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
        if re.search(self.PIDN,dicom_name):
            self.dcmheader.loc[0,"PIDN"] = self.PIDN
        else:
            self.dcmheader.loc[0,"PIDN"] = "CHECK HEADER"
        if re.search(self.visit,dicom_name):
            self.dcmheader.loc[0,"Visit"] = self.visit
        else:
            self.dcmheader.loc[0,"Visit"] = "CHECK HEADER"

        self.dcmheader.loc[0,"AcquisitionDate"] = pAcqDate
        self.dcmheader.loc[0,"PatientAge"] = pAge
        self.dcmheader.loc[0,"PatientSex"] = pSex
        self.dcmheader.loc[0,"ScannerID"] = pScanner
        
        if pScanner == "Ingenia" and "PixelData" in header:
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
        elif pScanner != "Ingenia":
            print "WARNING: %s/%s is scanned on %s, automatic processing not available!" % (root,dcmfile,pScanner)
        
        
        
        
        del header, dicom_name, pAcqDate,pSex,pAge,pScanner,pSeq

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
				self.R_exportloc = os.path.join(R_drive, "SEARCH RV398","%s_04_P%s" % (self.study,self.PIDN),"%s_04_P%s_%s" % (self.study,self.PIDN,self.visit))            


            ### Do Export Here ###
			if os.path.isdir(self.R_exportloc):
				print "EXPORT ERROR: %s already exists." % (self.R_exportloc)
			else:
				os.makedirs(self.R_exportloc)
				print ""
				print "EXPORTING %s %s %s to %s" % (self.study,self.PIDN,self.visit,self.R_exportloc)
				shutil.move(self.mri_dir,self.R_exportloc)
				if self.MRS_files:
					shutil.move(self.MRS_dir,self.R_exportloc)
				self.export_success = True
                ## return location for QCing ##
                #print 
				print "QC cmd: cd %s && \"%s\" %s && %\"%s\" %s && \"%s\" %s" % (os.path.join(self.R_exportloc,"mri_images"),
                                                             mricro_location, "Sag.T1W.3D/*.dcm",
                                                             mricro_location, "Ax\" \"FLAIR/*.dcm",
                                                             mricro_location, "Ax\" \"T2\" \"TSE/*.dcm")

                    
def run_import_steps(path):
    #path = "C:\Users\sf287610\Desktop\Compressed_Scans\SEARCH_2018-05-02"
    os.chdir(path)
    os.listdir(os.getcwd())
    holder = {name: SEARCH_study(name=name) for name in create_study_class(path)}
    print "=========================="
    print "   Local Processing...."
    print "=========================="
        
    ## Do unzipping and processing ##
    try:
        for i in holder:
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
    try:
        for i in holder:
            if holder[i].proceed:
                holder[i].do_export = raw_input(
                    "Export %s %s %s to R drive image archive? (y/n): " % (holder[i].study,holder[i].PIDN,holder[i].visit ))
                if holder[i].do_export == "y":
                    #holder[i].do_export == True
                    #print "    to export"
                    pass
                elif holder[i].do_export == "n":
                    #holder[i].do_export == False
                    print "    %s %s %s will not be exported" % (holder[i].study,holder[i].PIDN,holder[i].visit )
                else:
                    holder[i].do_export = raw_input("     Please enter (y/n): ")
            else:
            	print "Export not proceeding for %s %s %s" % (holder[i].study,holder[i].PIDN,holder[i].visit )
        print ""
        for i in holder:
            if holder[i].do_export == "y":
            	print "-----------------------"
            	print i
            	print "-----------------------"
                holder[i].R_export()
        print "R Drive Archive Export Done"

    except Exception as e:
        raise e
        pass

################################

scan_holder = run_import_steps(zipped_ftp_import_location)
run_archive_steps(scan_holder, zipped_ftp_import_location)