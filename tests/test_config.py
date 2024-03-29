import pytest

from amap.config.config import config_obj


@pytest.fixture()
def expected_conf():
    return {
        'affine': {
            'program_path': '',
            'n_steps': 6,
            'use_n_steps': 5
        },
        'freeform': {
            'program_path': '',
            'n_steps': 6,
            'use_n_steps': 4,
            'bending_energy_weight': 0.95,
            'grid_spacing': {'x': -10},
            'smoothing_sigma': {
                'reference': -1.0,
                'floating': -1.0
            },
            'histo_n_bins': {
                'reference': 128,
                'floating': 128
            }
        },
        'segmentation': {'program_path': ''},
        'atlas': {
            'base_folder': '~/.amap/atlas/',
            'default_atlas_name': 'allen_cff_october_2017_atlas_annotations_10_um.nii',
            'default_brain_name': 'allen_cff_october_2016_average_brain_filtered_10_um.nii',
            'default_hemispheres_name': 'allen_cff_october_2017_atlas_hemispheres_annotations_10_um.nii',
            'default_outlines_name': 'allen_cff_october_2017_atlas_outlines_10_um.nii',
            'atlas_path': '',
            'brain_path': '',
            'hemispheres_path': '',
            'outlines_path': '',
            'orientation': 'horizontal',
            'pixel_size': {
                'x': 0.010,
                'y': 0.010,
                'z': 0.010
            }
        }
    }


def test_config_obj(expected_conf):
    assert config_obj == expected_conf

