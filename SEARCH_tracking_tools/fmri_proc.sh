for i in P0299 P0307 P0339 P0353 P0363 P0370 P0382 P0408 P0423 P0440 P0524 P0528 P0539 P0545 P0546; do 
	#echo $i
	j=S010.${i}/S010.${i}_M0/mri_images
	outdir=/mnt/macdata/groups/valcour/kevin/SEARCH_export_20180629/${j}
	mkdir -p ${outdir}/T1
	mkdir -p ${outdir}/fMRI
	echo $j
	#ls $j/"Sag.T1W.3D"
	dcm2nii -a n -d n -e n -g n -i n -p n -f y -v n -o $outdir/T1 $j/"Sag.T1W.3D" 
	dcm2nii -a n -d n -e n -g n -i n -p n -f y -v n -o $outdir/fMRI $j/"Ax FFE.EPI"
done


############################

for i in 0061A 0063A 0064A 0065A 0066A 0067A 0071A 0072A 0073A; do 
j=${i}/M0/mri_images
outdir=/mnt/macdata/groups/valcour/kevin/SEARCH_export_20180629/S013A.${i}/S013A.${i}_M0/mri_images
mkdir -p ${outdir}/T1
mkdir -p ${outdir}/fMRI
echo $j
#ls $j/"Sag.T1W.3D"
dcm2nii -a n -d n -e n -g n -i n -p n -f y -v n -o $outdir/T1 $j/"Sag.T1W.3D" 
dcm2nii -a n -d n -e n -g n -i n -p n -f y -v n -o $outdir/fMRI $j/"Ax FFE.EPI"
done