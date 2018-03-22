import pytest

from amap.registration import registration_params


class RegistrationParamsMock(registration_params.RegistrationParams):
    def __init__(self):
        self.affine_reg_program_path = '/usr/local/bin/reg_aladin'
        self.freeform_reg_program_path = '/usr/local/bin/reg_f3d'
        self.segmentation_program_path = '/usr/local/bin/reg_resample'

        self.config = {
            'affine': '/usr/local/bin/reg_aladin',
            'freeform': '/usr/local/bin/reg_f3d',
            'segmentation': '/usr/local/bin/reg_resample'
        }

        self.affine_reg_pyramid_steps = ('-ln', 6)
        self.affine_reg_used_pyramid_steps = ('-lp', 5)

        self.freeform_reg_pyramid_steps = ('-ln', 6)
        self.freeform_reg_used_pyramid_steps = ('-lp', 4)

        self.freeform_reg_grid_spacing_x = ('-sx', -10)

        self.bending_energy_penalty_weight = ('-be', 0.95)

        self.reference_image_smoothing_sigma = ('-smooR', -1.0)
        self.floating_image_smoothing_sigma = ('-smooF', -0.0)

        self.reference_image_histo_n_bins = ('--rbn', 128)
        self.floating_image_histo_n_bins = ('--fbn', 128)

        self.default_atlas_path = '/home/lambda/amap/default_atlas.nii'
        self.atlas_path = '/home/lambda/amap/atlas.nii'
        self.atlas_brain_path = '/home/lambda/amap/atlas_brain.nii'
        self.hemispheres_path = '/home/lambda/amap/hemispheres_path.ini'
        self.atlas_x_pix_size = 0.01  # WARNING: mm
        self.atlas_y_pix_size = 0.01  # WARNING: mm
        self.atlas_z_pix_size = 0.01  # WARNING: mm


@pytest.fixture()
def params():
    return RegistrationParamsMock()


def test_format_affine_params(params):
    assert params.format_affine_params() == '-ln 6 -lp 5 '


def test_format_freeform_params(params):
    expected_output = '-ln 6 -lp 4 -sx -10 -be 0.95 -smooR -1.0 -smooF -0.0 --rbn 128 --fbn 128 '
    assert params.format_freeform_params() == expected_output


def test_format_segmentation_params(params):
    assert params.format_segmentation_params() == '-inter 0 '


def test_get_binary(params):
    pass
