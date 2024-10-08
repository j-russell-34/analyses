
# Write the column headers
echo SUBJECT,SESSION,left_nbm,right_nbm > /OUTPUTS/volumes.csv

# Iterate input subject/session
cd /INPUTS
for i in *;do
  cd /INPUTS/$i
  for j in *;do

    # Start new row with subject/session, end with comma
    echo -n "$i,$j," >> /OUTPUTS/volumes.csv

    # Get left volume, end with comma
    /REPO/ext/fslstats /INPUTS/$i/$j/assessors/*DnSeg_v1*/T1_seg_L.nii -V | awk '{printf $2","}' >> /OUTPUTS/volumes.csv

    # Get right volume, end with newline, no comma
    /REPO/ext/fslstats /INPUTS/$i/$j/assessors/*DnSeg_v1*/T1_seg_R.nii -V | awk '{printf $2"\n"}' >> /OUTPUTS/volumes.csv
  
  done
done
