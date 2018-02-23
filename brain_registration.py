import sys
import os

from brain_io import BrainIo
from registration_params import RegistrationParams
from run_command import safe_execute_command, SafeExecuteCommandError


class BrainRegistration(object):
    def __init__(self, sample_name, target_brain_path, output_folder):
        self.reg_params = self.get_reg_params()

        self.dataset_img_path = target_brain_path
        self.brain_of_atlas_img_path = self.reg_params.atlas_brain_path
        self.atlas_img_path = self.reg_params.atlas_path

        # TODO: put these suffixes in config
        self.affine_registered_img_path = os.path.join(output_folder,
                                                       '{}_affine_registered_atlas_brain.nii'.format(sample_name))
        self.freeform_registered_img_path = os.path.join(output_folder,
                                                         '{}_freeform_registered_atlas_brain.nii'.format(sample_name))
        self.registered_atlas_img_path = os.path.join(output_folder,
                                                      '{}_registered_atlas.nii'.format(sample_name))

        self.affine_matrix_path = os.path.join(output_folder,
                                               '{}_affine_matrix.txt'.format(sample_name))
        self.control_point_file_path = os.path.join(output_folder,
                                                    '{}_control_point_file.nii'.format(sample_name))

        log_file_template = os.path.join(output_folder, sample_name + '_{}.log')
        error_file_template = os.path.join(output_folder, sample_name + '_{}.err')

        self.affine_log_file_path = log_file_template.format('affine')  # TODO: erase if all is well ?
        self.affine_error_path = error_file_template.format('affine')

        self.freeform_log_file_path = log_file_template.format('freeform')
        self.freeform_error_file_path = error_file_template.format('freeform')

        self.segmentation_log_file = log_file_template.format('segment')
        self.segmentation_error_file = error_file_template.format('segment')

        # self.sanitise_inputs()

    def sanitise_inputs(self):
        img_paths_var_names = ('dataset_img_path', 'atlas_img_path', 'brain_of_atlas_img_path')
        for img_path_var_name in img_paths_var_names:
            img_path = getattr(self, img_path_var_name)
            if not os.path.exists(img_path):
                sys.exit('Cannot perform registration, image {} not found'.format(img_path))
            if not img_path.endswith('.nii'):
                if img_path.endswith(('.tiff', '.tif')):
                    nii_path = '{}{}'.format(os.path.splitext(img_path)[0], '.nii')
                    BrainIo.tiff_to_nii(img_path, nii_path)
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
