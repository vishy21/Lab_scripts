#on docker container, within DTI_TK folder:

TVtool -in inter_subjects_template.nii.gz -fa #creates inter_subjects_template_fa.nii.gz, template FA map in DTI-TK space, fit to the DTI-TK space template (the inter_subjects_template.nii.gz file)

fsl_reg $FSLDIR/data/atlases/JHU/JHU-ICBM-FA-1mm.nii.gz inter_subjects_template_fa.nii.gz atlas_to_DTITK_space -e -FA 
#RESULT: creates 1) warp for atlas to DTI-TK space (atlas_to_DTITK_space_warp.nii.gz), 2) matrix of linear warp (atlas_to_DTITK_space.mat), 3) atlas_to_DTITK_space.msf (don't know what this is)

#note: this warp is very close to the INVERSE of the warp matrix for the inter-subject template TO MNI/FSL space, but we don't want to have to create that warp and then just make an inverse of it and then apply it to the atlas
#so we are DIRECTLY creating a warp from atlas to DTI-TK space and then applying it to the atlas (next step)

applywarp -i $FSLDIR/data/atlases/JHU/JHU-ICBM-labels-1mm.nii.gz -o JHU_in_FA_inter_subjects_template -r inter_subjects_template_fa.nii.gz -w atlas_to_DTITK_space_warp.nii.gz -d float -s --superlevel=a --interp=nn 
#RESULT: outputs "JHU_in_FA_inter_subjects_template.nii.gz", a map of colorful (grayscale) ROIs of white matter tracts that are in your inter-template DTI-TK space 
#this will apply the warp, which was outputted by previous fsl_reg step, to the LABELs atlas so that you can extract ROIs from
#note: want to set interpolation to nearest neighbor to get strict boundaries between different ROIs in the atlas

#further note: JHU-ICBM-FA-1mm.nii.gz is an FA map in MNI/FSL space, JHU-ICBM-labels-1mm.nii.gz is a map of labeled colorful ROIs of white matter tracts you can use to extract ROI volumes from your images 

#you want to use the 1x1x1mm isotropic atlas instead of the 2x2x2 (smaller than the size of your template's voxels) --> ie you are taking the atlas and making the voxel size BIGGER (rather than taking your subject's DTI FA images and making their voxels larger)

# BEFORE starting following steps, I would suggest making a copy of all DTI...aff_diffeo_FA.nii.gz and the atlas in DTITK space, in case you do something wrong 
#in terminal, unzip the DTI...aff_diffeo_FA.nii.gz files for each participant, and the JHU_to_FA_inter_subjects_template.nii.gz that has all the ROIs in it, so you can use spm on them 

#%%%%%%%%% general concept to get an .nii image of a SINGLE roi %%%%%%%%%%%%%%%
#% A=spm_vol('JHU_to_FA_inter_subjects_template.nii');
#% Y=spm_read_vols(A);

#% infcerebpedR=(Y==11); %change variable_name, and value
#% B=A;
#% B.fname='infcerebpedR.nii'; %change to variable_name.nii
#% spm_write_vol(B, infcerebpedR); %change second variable of spm_write_vol to variable_name

#%%%%%%%%%%%%%% code to get nii image for all of the 48 DTI rois %%%%%%%%%%%%%%%%%%%%%%%

#%%%%% in MATLAB: so remove "#" from all lines %%%%%%%

################# CUT UP THE ATLAS INTO ITS ROI PIECES ########################

[rand JHU_names stuff]=xlsread('DTI_ROI_names.xls') 
length(JHU_names) #CHECK IS 48  

A=spm_vol('JHU_in_FA_inter_subjects_template.nii');
Y=spm_read_vols(A);

for i=1:length(JHU_names)
    x=JHU_names{i};
    x=(Y==i); 
    B=A;
    B.fname=strcat(JHU_names{i}, '.nii'); #%change to variable_name.nii
    spm_write_vol(B, x); #%change second variable of spm_write_vol to variable_name
end

#create .xls file with list of paths to FA images (name it "FA_img_paths.xls"), and another file with list of paths to atlas images (name "atlas_img_paths.xls")

############### USE THE ROI PIECES AND GET VOLUMES OF PARTICIPANTS AT THOSE ROIS ###############

#%%%%%%%%%%%% one way to create list of atlas_paths and FA_img_paths to iterate through: %%%%%%%%%%%%%
[ignore FA_img_paths this]=xlsread('FA_img_paths.xls')

[what atlas_img_paths ever]=xlsread('atlas_img_paths.xls')
#%atlas_img %use {} to index

#you can delete the "ignore, this, what, ever" variables from workspace if you'd like

length(FA_img_paths) #%check is number of participants
length(atlas_img_paths) #%check is number of atlas ROIs

mean_FAs=zeros(length(FA_img_paths), length(atlas_img_paths)); #%creates "mean_FAs" table, with each row as subject, each column as atlas ROI 

for i=1:length(FA_img_paths)
    for j=1:length(atlas_img_paths)
        [mean_FAs(i, j)] = mean(nonzeros(spm_summarise(FA_img_paths(i), atlas_img_paths{j})))
    end
end

csvwrite('mean_FA_vals.xls', mean_FAs) 




##############################################################################################
# get values from labels for each file 
for i in `ls`; do echo `ImageIntensityStatistics 3 ${i} ../templateandwarps/JHU_in_FA_inter_subjects_template.nii | awk '{print $2}'` ; done >> mean_MD.txt


##############################################################################################

Cingulum warp to 
