import os
import sys

from skimage import segmentation as sk_segmentation

from amap.brain import brain_io as bio

from amap.registration.registration_params import RegistrationParams
from amap.utils.run_command import safe_execute_command, SafeExecuteCommandError


class BrainRegistration(object):
    def __init__(self, sample_name, target_brain_path, output_folder):
        self.sample_name = sample_name
        self.output_folder = output_folder
        self.reg_params = self.get_reg_params()

        self.dataset_img_path = target_brain_path
        self.brain_of_atlas_img_path = self.reg_params.atlas_brain_path
        self.atlas_img_path = self.reg_params.atlas_path

        # TODO: put these suffixes in config
        self.affine_registered_img_path = self.make_path('{}_affine_registered_atlas_brain.nii')
        self.freeform_registered_img_path = self.make_path('{}_freeform_registered_atlas_brain.nii')
        self.registered_atlas_img_path = self.make_path('{}_registered_atlas.nii')

        self.affine_matrix_path = self.make_path('{}_affine_matrix.txt')
        self.control_point_file_path = self.make_path('{}_control_point_file.nii')

        self.outlines_file_path = self.make_path('{}_outlines.nii')

        self.affine_log_file_path, self.affine_error_path = self.compute_log_file_paths('affine')
        self.freeform_log_file_path, self.freeform_error_file_path = self.compute_log_file_paths('freeform')
        self.segmentation_log_file, self.segmentation_error_file = self.compute_log_file_paths('segment')

        # self.sanitise_inputs()

    def compute_log_file_paths(self, basename):
        log_file_template = os.path.join(self.output_folder, self.sample_name + '_{}.log')
        error_file_template = os.path.join(self.output_folder, self.sample_name + '_{}.err')
        log_file_path = log_file_template.format(basename)
        error_file_path = error_file_template.format(basename)
        return log_file_path, error_file_path

    def make_path(self, basename):
        return os.path.join(self.output_folder, basename.format(self.sample_name))

    def sanitise_inputs(self):
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
                    sys.exit('Cannot perform registration, image {} not in supported format'.format(img_path))

    def _prepare_affine_reg_cmd(self):
        cmd = '{} {} -flo {} -ref {} -aff {} -res {}'.format(
            self.reg_params.affine_reg_program_path, self.reg_params.format_affine_params().strip(),
            self.brain_of_atlas_img_path,
            self.dataset_img_path,
            self.affine_matrix_path,
            self.affine_registered_img_path
        )
        return cmd

    def register_affine(self):
        try:
            safe_execute_command(self._prepare_affine_reg_cmd(),
                                 self.affine_log_file_path, self.affine_error_path)
        except SafeExecuteCommandError as err:
            sys.exit('Affine registration failed; {}'.format(err))

    def _prepare_freeform_reg_cmd(self):
        cmd = '{} {} -aff {} -flo {} -ref {} -cpp {} -res {}'.format(
            self.reg_params.freeform_reg_program_path, self.reg_params.format_freeform_params().strip(),
            self.affine_matrix_path,
            self.brain_of_atlas_img_path,
            self.dataset_img_path,
            self.control_point_file_path,
            self.freeform_registered_img_path
        )
        return cmd

    def register_freeform(self):
        try:
            safe_execute_command(self._prepare_freeform_reg_cmd(),
                                 self.freeform_log_file_path, self.freeform_error_file_path)
        except SafeExecuteCommandError as err:
            sys.exit('Freeform registration failed; {}'.format(err))

    def _prepare_segmentation_cmd(self):
        cmd = '{} {} -cpp {} -flo {} -ref {} -res {}'.format(
            self.reg_params.segmentation_program_path, self.reg_params.format_segmentation_params().strip(),
            self.control_point_file_path,
            self.atlas_img_path,
            self.dataset_img_path,
            self.registered_atlas_img_path
        )
        return cmd

    def segment(self):
        try:
            safe_execute_command(self._prepare_segmentation_cmd(),
                                 self.segmentation_log_file, self.segmentation_error_file)
        except SafeExecuteCommandError as err:
            sys.exit('Segmentation failed; {}'.format(err))

    def get_reg_params(self):
        return RegistrationParams()

    def generate_outlines(self):
        morphed_atlas = bio.load_nii(self.registered_atlas_img_path, as_array=True)
        boundaries_mask = sk_segmentation.find_boundaries(morphed_atlas, mode='inner')
        boundaries = morphed_atlas * boundaries_mask
        bio.to_nii(boundaries, self.outlines_file_path, scale=(0.01, 0.01, 0.01))  # FIXME: should remove hard coding
