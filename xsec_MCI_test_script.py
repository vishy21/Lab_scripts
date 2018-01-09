#!python2
import pandas as pd
import numpy as np
import os




##################
##  Load files  ##
##################

# Load excel file with PIDNs as the label
master_data = raw_input("File name of Excel spreadsheet with data: ")

# Load text files with image path names for par.s we want
controls = raw_input("Text file with image paths for control participants: ")
dx = raw_input("Text file with image paths for dx participants: ")


par_data = pd.read_excel(master_data, index_col = "PIDN")
con_premerge = open(controls, 'r')
dx_premerge = open(dx, 'r')

###############################################
##  create PIDN lists from image file names  ##
###############################################

# Collects PIDNs from image path format mwWM_PIDN_DATE_MNI.nii.gz

PIDN_dx_lst = []
for i in dx_premerge:
    PIDN_1 = i.split("_",2)
    PIDN_dx_lst.append( int(PIDN_1[1]) )

PIDN_con_lst = []
for i in con_premerge:
    PIDN_2 = i.split("_",2)
    PIDN_con_lst.append( int(PIDN_2[1]) )

#print(PIDN_dx_lst)
#print(PIDN_con_lst)


#####################################
##  Merge two lists CONTROL first  ##
#####################################

PIDN_full = PIDN_con_lst + PIDN_dx_lst
#print(PIDN_full)
print len(PIDN_full), "total PIDNS merged, controls first"



###################################################
##  get means for Age, Gender, TIV, and Scanner  ##
###################################################

age_mean = np.mean(par_data["AgeAtDC"]) # **Age at DC, not current Age**
gender_mean = np.mean( par_data["Gender"]-1 ) # convert 1=M,2=F to 0=M,1=F
TIV_mean = np.mean( par_data["TIV"] )
scanner_mean = np.mean( par_data["ScannerID"] == "NIC 3T MRI PRISMA" ) #1 if PRISMA, 0 if not

#print(age_mean, gender_mean, TIV_mean, scanner_mean)


###########################################
##  create and fill rest of design file  ##
###########################################

# des1 = 1 for controls, 0 if dx
# des2 = 0 for controls, 1 if dx
# get mean centered values for PIDNs in our list in categories as defined above

# create empty design dataframe
des_df = pd.DataFrame(index=PIDN_full, columns=["des1","des2","Age","Gender","TIV","Scanner"])

# fill dataframe with information by PIDN lookup
for i in PIDN_full:
    des_df.loc[i]["Age"] = par_data.loc[i]["AgeAtDC"] - age_mean
    des_df.loc[i]["Gender"] = (par_data.loc[i]["Gender"] -1) - gender_mean
    des_df.loc[i]["TIV"] = par_data.loc[i]["TIV"] - TIV_mean
    des_df.loc[i]["Scanner"] = ( par_data.loc[i]["ScannerID"]== "NIC 3T MRI PRISMA" ) - scanner_mean
    des_df.loc[i]["des1"] = int( i in PIDN_con_lst )
    des_df.loc[i]["des2"] = int( i in PIDN_dx_lst )

#des_df

    
    
##################################################
##  print dataframe to tab-delimited text file  ##
##################################################

# If dataframe does not fill all the data:
if des_df.isnull().any().any():
    print "Error: Check you have all the data you need"
    

# Else: output design.txt file as created above
else:
    des_df.to_csv("Documents\Files_for_GLM_\design_test.txt", header=None, index=None, sep='\t')
    print "design_test.txt file created"
    # should overwrite previous design_test file if existing, need to check
    # needs cleanup to generalize code location??
    
    #np.savetxt("design_test.txt", des_df.values, fmt='%d')
    


######################################################
##  Bash shell script to merge files with fslmerge  ##
######################################################

# needs cleanup to generalize code

# change to True to run this
if False:
    cmd = """
    mkdir Stats_test
    mkdir Stats_test/Controls
    mkdir Stats_test/fullset
    mkdir Stats_test/MCI

    echo "made directories"

    for i in  `cat Controls_PIDNS_forfunction.txt`; do cp ${i} ./Stats_test/Controls; done

    echo "ready to merge first group"

    cd Stats_test/Controls

    fslmerge -t Controls_merged `ls`

    cp Controls_merged.nii.gz ../fullset/

    cd ../../

    for i in `cat MCI_PIDNS_forfunction.txt`; do cp ${i} ./Stats_test/MCI; done

    echo "ready to merge second group"

    cd Stats_test/MCI

    fslmerge -t MCI_merged `ls`

    cp MCI_merged.nii.gz ../fullset/

    cd ../../

    echo "merging full set"

    cd Stats_test/fullset

    fslmerge -t fullset_merged `ls`

    echo "completed" """

    proc = subprocess.Popen(cmd, shell=True)

    

    
    
# Test file locations
# Documents\Files_for_GLM_\X_section_MCI_for_stata.xlsx
# Documents\Files_for_GLM_\CON_premerge.txt
# Documents\Files_for_GLM_\MCI_PIDNs_premerge.txt




