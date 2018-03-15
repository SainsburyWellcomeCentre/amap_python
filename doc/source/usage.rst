Using aMAP
==========

Data Preparation
----------------

For the image registration to work, the image data needs to be in the Nifti format.
The Nifti format defines the default origin of the coordinate system as the most
ventral, posterior, left voxel of the dataset.
The positive axes are pointing away from that point, with x being left/right, y posterior/anterior and z ventral/dorsal:

Nifti Origin Illustration

The atlas's coordinate system respects this default and using input data with a different axes arrangement
will most likely result in failed segmentations. For comparability reasons, we further advise downsampling the images
to the resolution used in our study (12.5µm isotropically) prior to conversion and registration.
We have provided an example dataset in the testBrain folder showing a correctly oriented and formated Nifty file.
When setting the voxel dimensions, please note that Nifti uses mm as its unit.
Wrongly set units will cause the segmentation to fail.

The amap_python CLI should perform this scaling and orientation for you correctly provided you specify the scale
of the brain in mm.

Working with the result
-----------------------
Output files
************

aMAP will produce the following output files (sample_name is used as a placeholder for the dataset that is to be segmented):

:sample_name_freeform_registered_atlas_brain.nii:
    The average brain registered onto your sample (-res in niftyReg)
:sample_name_registered_atlas.nii:
    The atlas registered onto your sample (i.e. the segmentation of your sample.)
:sample_name_segmentation.nii:
    The borders of each structure registered onto your sample.
:sample_name_affine_matrix.txt:
    The transformation matrix describing the affine registration of the average brain to your sample (-aff in niftyReg)
:sample_name_control_point_file.nii:
    The the control-point grid describing the complete (affine and free-form) registration of the average brain
    to your sample.


Quality Control
***************

It is advisable to check all automated segmentations to ensure that the image registration worked correctly.
A convenient way is to overlay the structure borders of the segmentations (e.g. sample_name_segmentation.nii)
with the downscaled dataset that should be segmented (-ref in niftyReg).
Similarly, the registered average brain can be overlaid as well.
