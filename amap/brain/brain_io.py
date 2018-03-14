import os
import psutil

import numpy as np
from skimage import transform

import tifffile
import nibabel as nib
from tqdm import tqdm


class BrainIoLoadException(Exception):
    pass


def check_mem(img_byte_size, n_imgs):
    total_size = img_byte_size * n_imgs
    free_mem = psutil.virtual_memory().available
    if total_size >= free_mem:
        raise BrainIoLoadException('Not enough memory on the system to complete loading operation'
                                   'Needed {}, only {} available.'.format(total_size, free_mem))


def scale_z(volume, scaling_factor, verbose=False):
    if verbose:
        print('Scaling z dimension')
    volume = np.swapaxes(volume, 1, 2)
    volume = transform.rescale(volume, (1, scaling_factor), preserve_range=True)
    return np.swapaxes(volume, 1, 2)


# ######################## INPUT METHODS ####################
def load_any(src_path, x_scaling_factor=1.0, y_scaling_factor=1.0, z_scaling_factor=1.0, verbose=False):
    """
    .. warning:: x and y scaling not used at the moment if loading a complete image

    :param src_path:
    :param x_scaling_factor:
    :param y_scaling_factor:
    :param z_scaling_factor:
    :return:
    """
    if os.path.isdir(src_path):
        img = load_from_folder(src_path, x_scaling_factor, y_scaling_factor, name_filter='.tif')
    elif src_path.endswith('.txt'):
        img = load_img_sequence(src_path, x_scaling_factor, y_scaling_factor)
    elif src_path.endswith('.tif'):
        img = load_img_stack(src_path)
    elif src_path.endswith(('.nii', '.nii.gz')):
        img = load_nii(src_path)
    else:
        raise NotImplementedError('Could not guess loading method for path {}'.format(src_path))
    if z_scaling_factor != 1:
        img = scale_z(img, z_scaling_factor, verbose=verbose)
    return img


def load_img_stack(stack_path):
    stack = tifffile.imread(stack_path)   # FIXME: inverted dimensions
    # shape = stack.shape
    # out_stack = np.empty((shape[1], shape[2], shape[0]))
    # for i in range(shape[0]):  # FIXME: use reshape or swapaxis
    #     out_stack[:, :, i] = stack[i, :, :]
    # return out_stack
    return stack


def load_nii(src_path):  # FIXME: add option as_np_array=True (that returns .get_data())
    return nib.load(src_path)


def load_from_folder(src_folder, x_scaling_factor, y_scaling_factor, name_filter=''):
    paths = [os.path.join(src_folder, fname) for fname in sorted(os.listdir(src_folder)) if name_filter in fname]
    return load_from_paths_sequence(paths, x_scaling_factor, y_scaling_factor)


def load_img_sequence(img_sequence_file, x_scaling_factor, y_scaling_factor):
    with open(img_sequence_file, 'r') as in_file:
        paths = in_file.readlines()
        paths = [p.strip() for p in paths]
    return load_from_paths_sequence(paths, x_scaling_factor, y_scaling_factor)


def load_from_paths_sequence(paths_sequence, x_scaling_factor=1.0, y_scaling_factor=1.0):  # OPTIMISE: load threaded and process by batch
    for i, p in enumerate(tqdm(paths_sequence, desc='Loading images', unit='plane')):
        img = tifffile.imread(p)
        if i == 0:
            check_mem(img.nbytes * x_scaling_factor * y_scaling_factor, len(paths_sequence))
            volume = np.empty((int(round(img.shape[0] * x_scaling_factor)),
                               int(round(img.shape[1] * y_scaling_factor)),  # TODO: add test case for shape rounding
                               len(paths_sequence)),
                              dtype=img.dtype)
        if x_scaling_factor != 1 and y_scaling_factor != 1:
            # FIXME: see if needs filter with missing anti_aliasing
            img = transform.rescale(img,
                                    (x_scaling_factor, y_scaling_factor), mode='constant',
                                    preserve_range=True)
        volume[:, :, i] = img
    return volume


# ######################## OUTPUT METHODS ########################
def to_nii(img, dest_path, scale=(1, 1, 1), affine_transform=None):  # FIXME: add scale in metadata
    if affine_transform is None:
        affine_transform = np.eye(4)
    if not isinstance(img, nib.Nifti1Image):
        img = nib.Nifti1Image(img, affine_transform)
    if scale != (1, 1, 1):
        img.header.set_zooms(scale)
    nib.save(img, dest_path)


def tiff_to_nii(src_path, dest_path):
    if not dest_path.endswith('.nii.gz'):
        raise ValueError('Path is expected to end in "nii.gz", got {} instead.'.format(dest_path))

    img = load_any(src_path)
    if not isinstance(img, nib.Nifti1Image):
        img = nib.Nifti1Image(img, np.eye(4))
    nib.save(img, os.path.join(dest_path))  # FIXME: why os.path.join


def nii_to_tiff(src_path, dest_path):
    nii_img = load_nii(src_path)
    img = nii_img.get_data()
    tifffile.imsave(dest_path, img)


def to_tiff(img_volume, dest_path):
    tifffile.imsave(dest_path, img_volume)


def to_tiffs(img_volume, path_prefix, path_suffix='', pad_width=4):
    z_size = img_volume.shape[-1]
    if z_size > 10**pad_width:
        raise ValueError("Not enough padding digits {} for value {}".format(pad_width, z_size))
    for i in range(z_size):
        img = img_volume[:, :, i]
        dest_path = '{}_{}{}.tif'.format(path_prefix, str(i).zfill(pad_width), path_suffix)
        tifffile.imsave(dest_path, img)
