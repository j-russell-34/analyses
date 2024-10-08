# -*- coding: utf-8 -*-
"""
Spyder Editor
Author: Jason Russell.
Script to perform Voxel-wise linear regression between 2 PET tracers
"""

import glob
from nilearn import image
from nilearn import datasets
import os
import numpy as np
import statsmodels.api as sm
from nilearn.image import new_img_like
from nilearn.masking import compute_epi_mask
from nilearn import plotting
import nibabel as nib


PiB_files = glob.glob('/OUTPUTS/DATA/*/smoothed_warped_PIB.nii.gz')
FEOBV_files = glob.glob('/OUTPUTS/DATA/*/smoothed_warped_FEOBV.nii.gz')

#Set path where data is stored
data_path = '/OUTPUTS/DATA'
os.chdir(data_path)

#import generic T1 in MNI space to generate mask
dataset = datasets.fetch_icbm152_2009()

#restrict to voxels within the brain - NEED T1 MR IMAGE
#create brain mask
mask_img = compute_epi_mask(PiB_files[0])
brainmask = image.get_data(mask_img).astype(bool)

#Import smoothed/warped nifti files to generate 4D arrays
PiB_data = image.get_data(PiB_files)
FEOBV_data = image.get_data(FEOBV_files)

#get shapes of 4D arrays
dim1, dim2, dim3, subjects = PiB_data.shape

# Initialize arrays to store regression coefficients, p-values and intercepts
coefficients = np.zeros((dim1, dim2, dim3))
intercepts = np.zeros((dim1, dim2, dim3))
p_values = np.ones((dim1, dim2, dim3))

# Perform linear regression for each cell
for i in range(dim1):
    for j in range(dim2):
        for k in range(dim3):
            x = PiB_data[i, j, k, :].reshape(-1, 1)
            y = FEOBV_data[i, j, k, :]
            
            # Skip if all values in x or y are constant
            if np.all(x == x[0]) or np.all(y == y[0]):
                continue
                  
            # Add a column of ones for the intercept term
            x_with_intercept = sm.add_constant(x)
            
            # Create and fit the model
            model = sm.OLS(y, x_with_intercept).fit()
                
            # Store the coefficients and intercepts
            coefficients[i, j, k] = model.params[1]
            intercepts[i, j, k] = model.params[0] 
            p_values[i, j, k] = model.pvalues[1]

# pull unmasked coefficient values and output nifti



#apply brainmask to calculated coefficients
coef_brain = np.where(brainmask, coefficients, np.nan)

#create nifti of all coefficients
coefficients_nii = new_img_like(FEOBV_files[0], coefficients)
nib.save(coefficients_nii, "voxel-based_correlation_coef_unmasked.nii.gz")

# cut in x-direction
sagittal = -25
# cut in y-direction
coronal = -37
# cut in z-direction
axial = -6

# coordinates displaying should be prepared as a list
cut_coords = [sagittal, coronal, axial]

# Use a log scale for p-values
log_p_values = -np.log10(p_values)
# NAN values to zero
log_p_values[np.isnan(log_p_values)] = 0.0
log_p_values[log_p_values > 10.0] = 10.0
       
#generate mask if p<0.001
log_p_values[log_p_values < 3] = 0

# First argument being a reference image
# and second argument should be p-values data
# to convert to a new image as output.
# This new image will have same header information as reference image.   
#log_p_values_img = new_img_like('DST3050001/swFEOBV.nii', log_p_values)

# self-computed pval mask
bin_p_values = log_p_values != 0

bin_p_values_and_mask = np.logical_and(bin_p_values, brainmask)


#Generate Nifti image type
sig_p_mask_img = new_img_like(PiB_files[0], bin_p_values_and_mask.astype(int))


#apply mask to calculated coefficients
coef_masked = np.where(bin_p_values_and_mask, coefficients, np.nan)     


#create nifti of significant coefficients
sig_coefficients = new_img_like(FEOBV_files[0], coef_masked)


#generate mosiac plot of significant coefficients
plotting.plot_stat_map(sig_coefficients, display_mode="mosaic")


#export significant coefficients as nifti file
nib.save(sig_coefficients, "voxel-based_correlation.nii.gz")
