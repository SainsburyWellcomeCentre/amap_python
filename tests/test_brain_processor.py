import os

import numpy as np
import pytest

from amap.brain import brain_processor as bp


def test_normalise_to_16_bits():
    a = np.array([0, 2, 4, 240])
    b = bp.scale_to_16_bits(a)
    assert b.max() == (2**16 - 1)
    assert b.min() == 0
    assert b.shape == a.shape
    assert b[1] == pytest.approx(546.13, 0.1)


def test_pseudo_flatfield():
    pass


def test_despeckle_by_opening():
    pass


def test_filter_for_registration():
    pass


def test_get_atlas_pix_sizes(monkeypatch):
    from amap.config.config import config_obj
    monkeypatch.setitem(config_obj, 'atlas', {'path': os.path.join('..',
                                                                   'data',
                                                                   'atlas',
                                                                   'allen_cff_october_2017_atlas_annotations_10_um.nii')})
    for key, expected_key in zip(sorted(bp.get_atlas_pix_sizes().keys()), ('x', 'y', 'z')):
        assert key == expected_key
    assert (isinstance(v, float) for v in bp.get_atlas_pix_sizes().values())
