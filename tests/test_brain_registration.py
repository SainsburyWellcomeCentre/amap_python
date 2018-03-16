import pytest

from amap.registration import brain_registration
from test_registration_params import RegistrationParamsMock


class BrainRegMock(brain_registration.BrainRegistration):
    def get_reg_params(self):
        return RegistrationParamsMock()

    def sanitise_inputs(self):
        pass


@pytest.fixture
def brain_reg_fixture():
    sample_name = 'test_brain'
    target_brain_path = '/home/bob/brains/test_brain_downsampled.nii'
    output_folder = '/home/bob/output_brains/'
    reg = BrainRegMock(sample_name, target_brain_path, output_folder)
    return reg


def test_register_affine(brain_reg_fixture):
    expected_output = '/usr/local/bin/reg_aladin -ln 6 -lp 5 ' \
                      '-flo /home/lambda/amap/atlas_brain.nii -ref /home/bob/brains/test_brain_downsampled.nii ' \
                      '-aff /home/bob/output_brains/test_brain_affine_matrix.txt ' \
                      '-res /home/bob/output_brains/test_brain_affine_registered_atlas_brain.nii'
    assert brain_reg_fixture._prepare_affine_reg_cmd() == expected_output


def test_register_freeform(brain_reg_fixture):
    expected_output = '/usr/local/bin/reg_f3d -ln 6 -lp 4 -sx -10 -be 0.95 ' \
                      '-smooR -1.0 -smooF -0.0 --rbn 128 --fbn 128' \
                      ' -aff /home/bob/output_brains/test_brain_affine_matrix.txt' \
                      ' -flo /home/lambda/amap/atlas_brain.nii -ref /home/bob/brains/test_brain_downsampled.nii' \
                      ' -cpp /home/bob/output_brains/test_brain_control_point_file.nii' \
                      ' -res /home/bob/output_brains/test_brain_freeform_registered_atlas_brain.nii'
    assert brain_reg_fixture._prepare_freeform_reg_cmd() == expected_output


def test_segment(brain_reg_fixture):
    expected_output = '/usr/local/bin/reg_resample -inter 0 ' \
                      '-cpp /home/bob/output_brains/test_brain_control_point_file.nii ' \
                      '-flo /home/lambda/amap/atlas.nii -ref /home/bob/brains/test_brain_downsampled.nii ' \
                      '-res /home/bob/output_brains/test_brain_registered_atlas.nii'
    assert brain_reg_fixture._prepare_segmentation_cmd() == expected_output


def spike_generate_outlines():
    import numpy as np
    a = np.arange(10)
    b = np.array((True, False, False, False, True) * 2, dtype=np.bool)
    assert (a*b == np.array([0, 0, 0, 0, 4, 5, 0, 0, 0, 9])).all()
# assert error log is empty

