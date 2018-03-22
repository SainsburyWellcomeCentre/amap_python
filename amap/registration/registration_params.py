import os


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

        # FIXME: see if need to compute paths below if default
        atlas_config = self.config['atlas']

        self.default_atlas_path = os.path.abspath(os.path.join(*atlas_config['default_path']))
        self.default_atlas_brain_path = os.path.abspath(os.path.join(*atlas_config['default_brain_path']))
        self.default_hemispheres_path = os.path.abspath(os.path.join(*atlas_config['default_hemispheres_path']))
        cfg_atlas_path = atlas_config['path']
        self.atlas_path = cfg_atlas_path if cfg_atlas_path else self.default_atlas_path
        cfg_brain_path = atlas_config['brain_path']
        self.atlas_brain_path = cfg_brain_path if cfg_brain_path else self.default_atlas_brain_path
        cfg_hemispheres_path = atlas_config['hemispheres_path']
        self.hemispheres_path = cfg_hemispheres_path if cfg_hemispheres_path else self.default_hemispheres_path

        pixel_sizes = atlas_config['pixel_size']  # WARNING: mm
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
        from amap.config.config import os_folder_name
        nifty_reg_binaries_folder = os.path.abspath(os.path.join('.', 'niftyReg', 'bin', os_folder_name))

        program_names = {
            'affine': 'reg_aladin',
            'freeform': 'reg_f3d',
            'segmentation': 'reg_resample'
        }
        program_name = program_names[program_type]

        path_from_config = self.config[program_type]['program_path']
        if path_from_config:
            program_path = path_from_config
        else:
            program_path = os.path.join(nifty_reg_binaries_folder, program_name)

        return program_path
