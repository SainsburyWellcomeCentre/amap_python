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
NiftyReg being originally developed for MRI data, it uses the Neuroimaging Informatics Technology Initiative `(NIfTI)
image format <https://nifti.nimh.nih.gov/nifti-1/>`__ which is often referred to by its .nii file extension.

aMAP has been verified using a smoothed version of the atlas developed by
`Kim et al (2014) <http://www.cell.com/cell-reports/abstract/S2211-1247%2814%2901043-2>`__, (see below).
The structure associations for the brightness values in the segmentation file are noted in the accompanying .csv file
and follow the nomenclature of the Allen Mouse Brain Atlas.

aMAP consists of 4 parts:
    #. The main program (this repository)
    #. The binaries for the registration software (NiftyReg) (also included in this repository)
    #. The atlas used in the publication (which can be downloaded automatically by the installation script)
    #. Test data
