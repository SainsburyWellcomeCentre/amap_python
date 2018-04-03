import os

from amap.config.atlas import get_atlas_element_path, get_atlas_element_path_or_default, \
    get_atlas_pixel_sizes_from_config


class RegistrationParams(object):
    def __init__(self):
        from amap.config.config import config_obj  # Avoids import in tests
        self.config = config_obj

        self.affine_reg_program_path = self.__get_binary('affine')
        self.freeform_reg_program_path = self.__get_binary('freeform')
        self.segmentation_program_path = self.__get_binary('segmentation')

        self.affine_reg_pyramid_steps = ('-ln', self.config['affine']['n_steps'])
        self.affine_reg_used_pyramid_steps = ('-lp', self.config['affine']['use_n_steps'])

        freeform_config = self.config['freeform']
        self.freeform_reg_pyramid_steps = ('-ln', freeform_config['n_steps'])
        self.freeform_reg_used_pyramid_steps = ('-lp', freeform_config['use_n_steps'])

        self.freeform_reg_grid_spacing_x = ('-sx', freeform_config['grid_spacing']['x'])

        self.bending_energy_penalty_weight = ('-be', freeform_config['bending_energy_weight'])

        self.reference_image_smoothing_sigma = ('-smooR', freeform_config['smoothing_sigma']['reference'])
        self.floating_image_smoothing_sigma = ('-smooF', freeform_config['smoothing_sigma']['floating'])

        self.reference_image_histo_n_bins = ('--rbn', freeform_config['histo_n_bins']['reference'])
        self.floating_image_histo_n_bins = ('--fbn', freeform_config['histo_n_bins']['floating'])

        self.default_atlas_path = get_atlas_element_path('default_atlas_name')
        self.default_atlas_brain_path = get_atlas_element_path('default_brain_name')
        self.default_hemispheres_path = get_atlas_element_path('default_hemispheres_name')

        self.atlas_path = get_atlas_element_path_or_default('atlas_path')
        self.atlas_brain_path = get_atlas_element_path_or_default('brain_path')
        self.hemispheres_path = get_atlas_element_path_or_default('hemispheres_path')

        pixel_sizes = get_atlas_pixel_sizes_from_config()  # WARNING: mm
        self.atlas_x_pix_size = pixel_sizes['x']
        self.atlas_y_pix_size = pixel_sizes['y']
        self.atlas_z_pix_size = pixel_sizes['z']

    def get_affine_reg_params(self):
        affine_params = [
            self.affine_reg_pyramid_steps,
            self.affine_reg_used_pyramid_steps
        ]
        return affine_params

    def get_freeform_reg_params(self):
        freeform_params = [
            self.freeform_reg_pyramid_steps,
            self.freeform_reg_used_pyramid_steps,
            self.freeform_reg_grid_spacing_x,
            self.bending_energy_penalty_weight,
            self.reference_image_smoothing_sigma,
            self.floating_image_smoothing_sigma,
            self.reference_image_histo_n_bins,
            self.floating_image_histo_n_bins
        ]
        return freeform_params

    def get_segmentation_params(self):
        return [('-inter', 0), ]

    def format_param_pairs(self, params_pairs):
        """
        Format the list of params pairs into a string

        :param list params_pairs: A list of tuples of the form (option_string, option_value) (e.g. (-sx, 10))
        :return:
        """
        out = ''
        for param in params_pairs:
            out += '{} {} '.format(*param)
        return out

    def format_affine_params(self):
        return self.format_param_pairs(self.get_affine_reg_params())

    def format_freeform_params(self):
        return self.format_param_pairs(self.get_freeform_reg_params())

    def format_segmentation_params(self):
        return self.format_param_pairs(self.get_segmentation_params())

    def __get_binary(self, program_type):
        from amap.config.config import get_binary
        program_names = {
            'affine': 'reg_aladin',
            'freeform': 'reg_f3d',
            'segmentation': 'reg_resample'
        }
        program_name = program_names[program_type]
        nifty_reg_binaries_folder = 'amap/bin/nifty_reg'

        path_from_config = self.config[program_type]['program_path']
        if path_from_config:
            program_path = path_from_config
        else:
            program_path = get_binary(nifty_reg_binaries_folder, program_name)  # TODO: add to cfg

        return program_path
