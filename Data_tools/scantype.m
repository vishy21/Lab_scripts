tic
X = 'MR0001_0.dcm'; 
info = dicominfo(X); 
Scan_type = info.SeriesDescription
Slices =info.NumberOfFrames
Flip = info.SharedFunctionalGroupsSequence.Item_1.MRTimingAndRelatedParametersSequence.Item_1.FlipAngle
ETL = info.PerFrameFunctionalGroupsSequence.Item_1.Private_2005_140f.Item_1.EchoTrainLength
TE = info.PerFrameFunctionalGroupsSequence.Item_1.Private_2005_140f.Item_1.EchoTime
TR = info.SharedFunctionalGroupsSequence.Item_1.MRTimingAndRelatedParametersSequence.Item_1.RepetitionTime
TI = info.InversionTime
Acquisitiontime = info.AcquisitionDuration/60
Space_between = info.SpacingBetweenSlices
Pixel_size = info.PerFrameFunctionalGroupsSequence.Item_1.Private_2005_140f.Item_1.PixelSpacing
SliceThickness = info.PerFrameFunctionalGroupsSequence.Item_1.Private_2005_140f.Item_1.SliceThickness
Num_averages = info.PerFrameFunctionalGroupsSequence.Item_1.Private_2005_140f.Item_1.NumberOfAverages
Time_points = info.PerFrameFunctionalGroupsSequence.Item_1.Private_2005_140f.Item_1.NumberOfTemporalPositions
Row_FOV = info.Rows
Col_FOV = info.Columns
b_value = info.PerFrameFunctionalGroupsSequence.Item_2.MRDiffusionSequence.Item_1.DiffusionBValue
paralell = info.ParallelAcquisitionTechnique
R = info.ParallelReductionFactorInPlane
Vox = [Pixel_size(1,1) Pixel_size(2,1) SliceThickness]
toc

T1 = {[TR TE],Flip,Vox,Slices,'no gap',Acquisitiontime}'
DTI = { [TR TE],Num_averages, [Row_FOV Col_FOV], [paralell R], ETL, Vox,'32 directions', b_value, Slices, 'no gap', Acquisitiontime}'
FLair =  {[TR TE],TI,Vox,Slices,SliceThickness,'no gap',Acquisitiontime}'
