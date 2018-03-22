import os
import pytest

import numpy as np
from tifffile import tifffile

from amap.brain import brain_io as bio


@pytest.fixture()
def layer():
    return np.tile(np.array([1, 2, 3, 4]), (4, 1))


@pytest.fixture()
def start_array(layer):
    volume = np.dstack((layer, 2 * layer, 3 * layer, 4 * layer))
    return volume


def test_tiff_io(tmpdir, layer):
    folder = str(tmpdir)
    dest_path = os.path.join(folder, 'layer.tiff')
    tifffile.imsave(dest_path, layer)
    reloaded = tifffile.imread(dest_path)
    # print("Original image:\n {}".format(layer))
    # print("Reloaded image:\n {}".format(reloaded))
    assert (reloaded == layer).all()


def test_to_tiffs(tmpdir, start_array):
    folder = str(tmpdir)
    bio.to_tiffs(start_array, os.path.join(folder, 'start_array'))
    reloaded_array = bio.load_from_folder(folder, 1, 1)
    assert (reloaded_array == start_array).all()


def test_load_img_sequence(tmpdir, start_array):
    folder = str(tmpdir.mkdir('sub'))
    bio.to_tiffs(start_array, os.path.join(folder, 'start_array'))
    img_sequence_file = tmpdir.join('imgs_file.txt')
    img_sequence_file.write("\n".join([os.path.join(folder, fname) for fname in sorted(os.listdir(folder))]))
    reloaded_array = bio.load_img_sequence(str(img_sequence_file), 1, 1)
    assert (reloaded_array == start_array).all()


def test_to_nii(tmpdir, start_array):  # Also tests load_nii
    folder = str(tmpdir)
    nii_path = os.path.join(folder, 'test_array.nii')
    bio.to_nii(start_array, nii_path)
    assert (bio.load_nii(nii_path).get_data() == start_array).all()


def test_nii_to_tiff(tmpdir, start_array):
    nii_path = os.path.join(str(tmpdir), 'test_array.nii.gz')
    tiff_path = os.path.join(str(tmpdir), 'test_array.tiff')

    bio.to_nii(start_array, nii_path)
    bio.nii_to_tiff(nii_path, tiff_path)
    test_array = bio.load_img_stack(tiff_path)

    # print("Start array:\n {}".format(start_array))
    # print("Test array:\n {}".format(test_array))
    assert (test_array == start_array).all()


def test_tiff_to_nii(tmpdir, start_array):
    tiffs_folder = str(tmpdir.mkdir('tiffs'))
    bio.to_tiffs(start_array, os.path.join(tiffs_folder, 'start_array'))
    nii_path = os.path.join(str(tmpdir), 'test_array.nii.gz')
    bio.tiff_to_nii(tiffs_folder, nii_path)
    assert (bio.load_nii(nii_path).get_data() == start_array).all()


def test_scale_z(start_array):
    assert bio.scale_z(start_array, 0.5).shape[-1] == start_array.shape[-1] / 2
    assert bio.scale_z(start_array, 2).shape[-1] == start_array.shape[-1] * 2
