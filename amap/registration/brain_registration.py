"""
brain_registration
==================

The module to actually start the registration
"""
import os
import sys

import numpy as np
from skimage import segmentation as sk_segmentation

from amap.brain import brain_io as bio

from amap.registration.registration_params import RegistrationParams
from amap.utils.run_command import safe_execute_command, SafeExecuteCommandError


class RegistrationError(Exception):
    pass


class SegmentationError(RegistrationError):
    pass


def make_atlas_mask(atlas_img_path, mask_path, atlas_start_slice, atlas_end_slice):
    atlas = bio.load_nii(atlas_img_path, as_array=False)
    atlas_mask = atlas.get_data().astype(np.uint16)

    mask_low_value = 0
    mask_high_value = 2**16 - 1
    atlas_mask[:, :atlas_start_slice, :] = mask_low_value  # FIXME: only valid for horizontal atlas
    atlas_mask[:, atlas_start_slice:atlas_end_slice, :] = mask_high_value
    atlas_mask[:, atlas_end_slice:, :] = mask_low_value
    bio.to_nii(atlas, mask_path)


class BrainRegistration(object):
    """
    A class to register brains using the nifty_reg set of binaries
    """
    def __init__(self, sample_name, target_brain_path, output_folder, atlas_start_slice=0, atlas_end_slice=-1):
        self.sample_name = sample_name
        self.output_folder = output_folder
        self.reg_params = self.get_reg_params()

        self.dataset_img_path = target_brain_path
        self.brain_of_atlas_img_path = self.reg_params.atlas_brain_path
        self.atlas_img_path = self.reg_params.atlas_path
        self.hemispheres_img_path = self.reg_params.hemispheres_path

        if atlas_start_slice != 0 or atlas_end_slice != -1:
            make_atlas_mask(self.atlas_img_path,
                            self.reg_params.atlas_mask_path,
                            atlas_start_slice, atlas_end_slice)
            self.atlas_mask_path = self.reg_params.atlas_mask_path
        else:
            self.atlas_mask_path = ''

        # TODO: put these suffixes in config
        self.affine_registered_img_path = self.make_path('{}_affine_registered_atlas_brain.nii')
        self.freeform_registered_img_path = self.make_path('{}_freeform_registered_atlas_brain.nii')
        self.registered_atlas_img_path = self.make_path('{}_registered_atlas.nii')
        self.registered_hemispheres_img_path = self.make_path('{}_registered_hemispheres.nii')

        self.affine_matrix_path = self.make_path('{}_affine_matrix.txt')
        self.control_point_file_path = self.make_path('{}_control_point_file.nii')

        self.outlines_file_path = self.make_path('{}_outlines.nii')

        self.affine_log_file_path, self.affine_error_path = self.compute_log_file_paths('affine')
        self.freeform_log_file_path, self.freeform_error_file_path = self.compute_log_file_paths('freeform')
        self.segmentation_log_file, self.segmentation_error_file = self.compute_log_file_paths('segment')

        # self.sanitise_inputs()

    def compute_log_file_paths(self, basename):
        """
        Compute the path of the log and err file for the step corresponding to basename

        :param str basename:
        :return: log_file_path, error_file_path
        """
        log_file_template = os.path.join(self.output_folder, self.sample_name + '_{}.log')
        error_file_template = os.path.join(self.output_folder, self.sample_name + '_{}.err')
        log_file_path = log_file_template.format(basename)
        error_file_path = error_file_template.format(basename)
        return log_file_path, error_file_path

    def make_path(self, basename):
        """
        Compute the absolute path of the destination file to self.output_folder using the
        sample_name attribute.

        :param str basename:
        :return: The path
        :rtype: str
        """
        return os.path.join(self.output_folder, basename.format(self.sample_name))

    def sanitise_inputs(self):
        """
        Validates the inputs paths (dataset, atlas, brain of atlas) to check that they are the
        correct image type and that they exist.

        :return:
        :raises RegistrationError: If the conditions are not met
        """
        img_paths_var_names = ('dataset_img_path', 'atlas_img_path', 'brain_of_atlas_img_path')
        for img_path_var_name in img_paths_var_names:
            img_path = getattr(self, img_path_var_name)
            if not os.path.exists(img_path):
                sys.exit('Cannot perform registration, image {} not found'.format(img_path))
            if not img_path.endswith('.nii'):
                if img_path.endswith(('.tiff', '.tif')):
                    nii_path = '{}{}'.format(os.path.splitext(img_path)[0], '.nii')
                    bio.tiff_to_nii(img_path, nii_path)
                    setattr(self, img_path_var_name, nii_path)
                else:
                    raise RegistrationError('Cannot perform registration, image {} not in supported format'
                                            .format(img_path))

    def _prepare_affine_reg_cmd(self):
        cmd = '{} {} -flo {} -ref {} -aff {} -res {}'.format(
            self.reg_params.affine_reg_program_path, self.reg_params.format_affine_params().strip(),
            self.brain_of_atlas_img_path,
            self.dataset_img_path,
            self.affine_matrix_path,
            self.affine_registered_img_path
        )
        if self.atlas_mask_path:
            cmd += ' -fmask {}'.format(self.atlas_mask_path)
        return cmd

    def register_affine(self):
        """
        Performs affine registration of the average brain of the atlas to the sample brain
        using nifty_reg reg_aladin

        :return:
        :raises RegistrationError: If any error was detected during registration.
        """
        try:
            safe_execute_command(self._prepare_affine_reg_cmd(),
                                 self.affine_log_file_path, self.affine_error_path)
        except SafeExecuteCommandError as err:
            raise RegistrationError('Affine registration failed; {}'.format(err))

    def _prepare_freeform_reg_cmd(self):
        cmd = '{} {} -aff {} -flo {} -ref {} -cpp {} -res {}'.format(
            self.reg_params.freeform_reg_program_path, self.reg_params.format_freeform_params().strip(),
            self.affine_matrix_path,
            self.brain_of_atlas_img_path,
            self.dataset_img_path,
            self.control_point_file_path,
            self.freeform_registered_img_path
        )
        if self.atlas_mask_path:
            cmd += ' -fmask {}'.format(self.atlas_mask_path)
        return cmd

    def register_freeform(self):
        """
        Performs freeform (elastic) registration of the average brain of the atlas to the sample brain
        using nifty_reg reg_f3d

        :return:
        :raises RegistrationError: If any error was detected during registration.
        """
        try:
            safe_execute_command(self._prepare_freeform_reg_cmd(),
                                 self.freeform_log_file_path, self.freeform_error_file_path)
        except SafeExecuteCommandError as err:
            raise RegistrationError('Freeform registration failed; {}'.format(err))

    def _prepare_segmentation_cmd(self, floating_image_path, dest_img_path):
        cmd = '{} {} -cpp {} -flo {} -ref {} -res {}'.format(
            self.reg_params.segmentation_program_path, self.reg_params.format_segmentation_params().strip(),
            self.control_point_file_path,
            floating_image_path,
            self.dataset_img_path,
            dest_img_path
        )
        return cmd

    def segment(self):
        """
        Registers the atlas to the sample brain (propagates the transformation computed for the average brain
        of the atlas to the atlas itself).


        :return:
        :raises SegmentationError: If any error was detected during the propagation.
        """
        try:
            safe_execute_command(self._prepare_segmentation_cmd(self.atlas_img_path, self.registered_atlas_img_path),
                                 self.segmentation_log_file, self.segmentation_error_file)
        except SafeExecuteCommandError as err:
            SegmentationError('Segmentation failed; {}'.format(err))

    def register_hemispheres(self):
        """
        Registers the hemispheres atlas to the sample brain (propagates the transformation computed for the average brain
        of the atlas to the hemispheres atlas itself).

        :return:
        :raises RegistrationError: If any error was detected during the propagation.
        """
        try:
            safe_execute_command(self._prepare_segmentation_cmd(self.hemispheres_img_path,
                                                                self.registered_hemispheres_img_path),
                                 self.segmentation_log_file, self.segmentation_error_file)
        except SafeExecuteCommandError as err:
            SegmentationError('Segmentation failed; {}'.format(err))

    def get_reg_params(self):
        """
        Returns the registration params. Mostly used to simplify tests setup

        :return: The registration params
        :rtype: RegistrationParams
        """
        return RegistrationParams()

    def generate_outlines(self):
        """
        Generates the outlines of the different atlas region.

        :return:
        """
        morphed_atlas = bio.load_nii(self.registered_atlas_img_path, as_array=False)
        atlas_scale = morphed_atlas.header.get_zooms()
        morphed_atlas = morphed_atlas.get_data()
        boundaries_mask = sk_segmentation.find_boundaries(morphed_atlas, mode='inner')
        boundaries = morphed_atlas * boundaries_mask
        bio.to_nii(boundaries, self.outlines_file_path, scale=atlas_scale)
