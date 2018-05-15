"""
registration_params
===================

The module to handle all the registration options and program binaries
"""
from amap.config.atlas import Atlas


class RegistrationParams(object):
    """
    A class to store and access the variables required for the registration
    including the paths of the different binaries and atlases.
    Options are typically stored as a tuple of (option_string, option_value)
    """
    def __init__(self, output_folder=''):
        from amap.config.config import config_obj  # Avoids import in tests
        self.config = config_obj

        self.affine_reg_program_path = self.__get_binary('affine')
        self.freeform_reg_program_path = self.__get_binary('freeform')
        self.segmentation_program_path = self.__get_binary('segmentation')
        self.deformation_program_path = self.__get_binary('deformation')

        # affine (reg_aladin)
        self.affine_reg_pyramid_steps = ('-ln', self.config['affine']['n_steps'])
        self.affine_reg_used_pyramid_steps = ('-lp', self.config['affine']['use_n_steps'])

        # freeform (ref_f3d)
        freeform_config = self.config['freeform']
        self.freeform_reg_pyramid_steps = ('-ln', freeform_config['n_steps'])
        self.freeform_reg_used_pyramid_steps = ('-lp', freeform_config['use_n_steps'])

        self.freeform_reg_grid_spacing_x = ('-sx', freeform_config['grid_spacing']['x'])

        self.bending_energy_penalty_weight = ('-be', freeform_config['bending_energy_weight'])

        self.reference_image_smoothing_sigma = ('-smooR', freeform_config['smoothing_sigma']['reference'])
        self.floating_image_smoothing_sigma = ('-smooF', freeform_config['smoothing_sigma']['floating'])

        self.reference_image_histo_n_bins = ('--rbn', freeform_config['histo_n_bins']['reference'])
        self.floating_image_histo_n_bins = ('--fbn', freeform_config['histo_n_bins']['floating'])

        # segmentation (reg_resample)
        self.segmentation_interpolation_order = ('-inter', 0)

        atlas = Atlas(src_folder=output_folder)  # The atlas has been saved to the output folder

        self.default_atlas_path = atlas.get_default_atlas_path()
        self.default_atlas_brain_path = atlas.get_default_brain_path()
        self.default_hemispheres_path = atlas.get_default_hemispheres_path()

        self.atlas_path = atlas.get_path()
        self.atlas_brain_path = atlas.get_brain_path()
        self.hemispheres_path = atlas.get_hemispheres_path()
        self.atlas_mask_path = atlas.get_mask_path()

        pixel_sizes = atlas.get_pixel_sizes_from_config()  # WARNING: mm
        self.atlas_x_pix_size = pixel_sizes['x']
        self.atlas_y_pix_size = pixel_sizes['y']
        self.atlas_z_pix_size = pixel_sizes['z']

    def get_affine_reg_params(self):
        """
        Get the parameters (options) required for the affine registration step

        :return: The affine registration options.
        :rtype: list
        """
        affine_params = [
            self.affine_reg_pyramid_steps,
            self.affine_reg_used_pyramid_steps
        ]
        return affine_params

    def get_freeform_reg_params(self):
        """
        Get the parameters (options) required for the freeform (elastic) registration step

        :return: The freeform registration options.
        :rtype: list
        """
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
        """
        Get the parameters (options) required for the segmentation step (propagation of transformation)

        :return: The affine registration options.
        :rtype: list
        """
        return [self.segmentation_interpolation_order, ]

    def format_param_pairs(self, params_pairs):
        """
        Format the list of params pairs into a string

        :param list params_pairs: A list of tuples of the form (option_string, option_value) (e.g. (-sx, 10))
        :return: The options as a formatted string
        :rtype: str
        """
        out = ''
        for param in params_pairs:
            out += '{} {} '.format(*param)
        return out

    def format_affine_params(self):
        """
        Generate the string of formatted affine registration options

        :return: The formatted string
        :rtype: str
        """
        return self.format_param_pairs(self.get_affine_reg_params())

    def format_freeform_params(self):
        """
        Generate the string of formatted freeform registration options

        :return: The formatted string
        :rtype: str
        """
        return self.format_param_pairs(self.get_freeform_reg_params())

    def format_segmentation_params(self):
        """
        Generate the string of formatted segmentation options

        :return: The formatted string
        :rtype: str
        """
        return self.format_param_pairs(self.get_segmentation_params())

    def __get_binary(self, program_type):
        """
        Get the path to the registration (from nifty_reg) program based on the type

        :param str program_type:
        :return: The program path
        :rtype: str
        """
        from amap.config.config import get_binary
        program_names = {
            'affine': 'reg_aladin',
            'freeform': 'reg_f3d',
            'segmentation': 'reg_resample',
            'deformation': 'reg_transform'
        }
        program_name = program_names[program_type]
        nifty_reg_binaries_folder = 'amap/bin/nifty_reg'

        path_from_config = self.config[program_type]['program_path']
        if path_from_config:
            program_path = path_from_config
        else:
            program_path = get_binary(nifty_reg_binaries_folder, program_name)  # TODO: add to cfg

        return program_path
