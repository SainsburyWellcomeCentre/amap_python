Welcome to the aMAP companion guide
===================================
This guide contains all the information needed to perform automated mouse atlas propagation on full-brain 3D datasets.
If you have any questions regarding this manual or run into any issues trying to use aMAP, please contact
me at c.rousseau[at]ucl.ac.uk


What is aMAP
============

aMAP is a tool for optimized automated mouse atlas propagation based on clinical registration software
(`NiftyReg <http://cmictig.cs.ucl.ac.uk/research/software/software-nifty/niftyreg>`__) for anatomical segmentation
of high-resolution 3D fluorescence images of the adult mouse brain.
aMAP permits propagation of a 3D mouse atlas of the entire adult mouse brain in 40 min and its accuracy and
reliability is shown to be on par with expert human raters
`(publication) <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4941048/>`__.
aMAP, internally uses NiftyReg (a rapid image registration toolkit, originally developed for human MRI data),
that we modified to enable rapid processing of high-resolution 3D light microscopy data.
NiftyReg being originally developed for MRI data, it uses the Neuroimaging Informatics Technology Initiative (NIfTI)
image format which is often referred to by its .nii file extension.

aMAP has been verified using a smoothed version of the atlas developed by
`Kim et al (2014) <http://www.cell.com/cell-reports/abstract/S2211-1247%2814%2901043-2>`__, (see below).
The structure associations for the brightness values in the segmentation file are noted in the accompanying .csv file
and follow the nomenclature of the Allen Mouse Brain Atlas.

aMAP consists of 4 parts:
    #. The main program (this repository)
    #. The binaries for the registration software (NiftyReg)
    #. The atlas used in the publication
    #. Test data


Prerequisites
=============

.. note::

    Segmentation requires a powerful machine.
    A workstation computer (e.g. Mac Pro or Dell Precision) with at least 16GB of RAM is necessary.
    For smooth viewing of .nii fils in matlab, we recommend at least 24GB of RAM.

aMAP has been tested on Mac (OS X Yosemite) and Linux (Debian Jessie) machines, for which binaries are provided.
The NiftyReg command line interface has been designed to also run on Windows, but this has not yet been tested by us
and will require compilation from source.


Image viewer
------------

An image viewer is necessary to check the output of the registration. Recommended are Fiji/ImageJ or ICY.

.. note::

    Although Fiji can currently load .nii images, it is currently unable to save them.



Installing aMAP
===============

To install aMAP:
    #. Download or clone this repository
    #. If you downloaded the repository, extract the archive.
    #. Download the `NiftyReg binaries <http://www.gatsby.ucl.ac.uk/%7Etest/aMAP-0.0.1.tar.gz>`__
    #. Place these binaries inside the amap_python folder under amap_python;niftyReg;bin;
        (the semi-colon represents the file separator on your operating system)
    #. Download the atlas and place it under amap_python;data;atlas;
    #. If required download the test data


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

Running the program
-------------------

The program currently only provides a command line interface. The defaults for the CLI and the paths to the programs and
atlas if these do not use the location recommended in the installation instructions can be modified in a text based
configuration file that you will find under amap;config;amap.conf

To run the program, use:

.. automodule:: amap.main


.. argparse::
    :module: amap.main
    :func: get_parser
    :prog: amap_cli


Working with the result
-----------------------
Output files
************

aMAP will produce the following output files (sample_name is used as a placeholder for the dataset that is to be segmented):

:sample_name_freeform_registered_atlas_brain.nii:
    The average brain registered onto your sample (-res in niftyReg)
:sample_name_registered_atlas.nii:
    The atlas registered onto your sample (i.e. the segmentation of your sample.)
:sample_name_outlines.nii:
    The borders of each structure registered onto your sample.
:sample_name_affine_matrix.txt:
    The transformation matrix describing the affine registration of the average brain to your sample (-aff in niftyReg)
:sample_name_control_point_file.nii:
    The the control-point grid describing the complete (affine and free-form) registration of the average brain
    to your sample.


Quality Control
***************

It is advisable to check all automated segmentations to ensure that the image registration worked correctly.
A convenient way is to overlay the structure borders of the segmentations (e.g. sample_name_outlines.nii)
with the downscaled dataset that should be segmented (-ref in niftyReg).
Similarly, the registered average brain can be overlaid as well.


