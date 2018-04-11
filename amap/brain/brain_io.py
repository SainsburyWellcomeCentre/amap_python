"""
A module to load and save 'brains' (image 3D volumes) as either nifty image files, tiff stacks or sequences of
tiffs either from the folder they are stored in or a file containing a sorted list of file paths
"""
import os
import math
import psutil
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor

import warnings

import numpy as np
from skimage import transform

import tifffile
import nibabel as nib
from tqdm import tqdm


class BrainIoLoadException(Exception):
    pass


def check_mem(img_byte_size, n_imgs):
    """
    Check how much memory is available on the system and compares it to the size
    the stack specified by img_byte_size and n_imgs would take once loaded

    Raises an error in case memory is insufficient to load that stack

    :param int img_byte_size:
    :param int n_imgs:
    :return:
    :raises: BrainLoadException if not enough memory is available
    """
    total_size = img_byte_size * n_imgs
    free_mem = psutil.virtual_memory().available
    if total_size >= free_mem:
        raise BrainIoLoadException('Not enough memory on the system to complete loading operation'
                                   'Needed {}, only {} available.'.format(total_size, free_mem))


def scale_z(volume, scaling_factor, verbose=False):
    """
    Scale the given brain allong the z dimension

    :param np.ndarray volume: A brain typically as a numpy array
    :param float scaling_factor:
    :param bool verbose:
    :return:
    """
    if verbose:
        print('Scaling z dimension')
    volume = np.swapaxes(volume, 1, 2)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        volume = transform.rescale(volume, (1, scaling_factor), preserve_range=True)
    return np.swapaxes(volume, 1, 2)


# ######################## INPUT METHODS ####################
def load_any(src_path, x_scaling_factor=1.0, y_scaling_factor=1.0, z_scaling_factor=1.0,
             load_parallel=False, verbose=False):
    """
    Load the brain specified by
    This function will guess the type of data and hence call the appropriate
    function from this module to load the given brain.

    .. warning:: x and y scaling not used at the moment if loading a complete image

    :param str src_path: Can be the path of a nifty file, tiff file, tiff files folder or text file containing a list of paths
    :param float x_scaling_factor: The scaling of the brain along the x dimension (applied on loading before return)
    :param float y_scaling_factor: The scaling of the brain along the y dimension (applied on loading before return)
    :param float z_scaling_factor: The scaling of the brain along the z dimension (applied on loading before return)
    :param bool load_parallel:
    :param bool verbose:
    :return: The loaded brain
    :rtype: np.ndarray
    """
    if os.path.isdir(src_path):
        img = load_from_folder(src_path, x_scaling_factor, y_scaling_factor,
                               name_filter='.tif', load_parallel=load_parallel)
    elif src_path.endswith('.txt'):
        img = load_img_sequence(src_path, x_scaling_factor, y_scaling_factor, load_parallel=load_parallel)
    elif src_path.endswith('.tif'):
        img = load_img_stack(src_path)
    elif src_path.endswith(('.nii', '.nii.gz')):
        img = load_nii(src_path, as_array=True)
    else:
        raise NotImplementedError('Could not guess loading method for path {}'.format(src_path))
    if z_scaling_factor != 1:
        img = scale_z(img, z_scaling_factor, verbose=verbose)
    return img


def load_img_stack(stack_path):
    """
    Load a tiff stack as a numpy array

    :param str stack_path: The path of the image to be loaded
    :return: The loaded brain array
    :rtype: np.ndarray
    """
    stack = tifffile.imread(stack_path)
    # shape = stack.shape
    # out_stack = np.empty((shape[1], shape[2], shape[0]))
    # for i in range(shape[0]):  # should use swapaxes
    #     out_stack[:, :, i] = stack[i, :, :]
    # return out_stack
    return stack


def load_nii(src_path, as_array=False):
    """
    Load a brain from a nifty file

    :param str src_path: The path to the nifty file on the filesystem
    :param bool as_array: Whether to convert the brain to a numpy array of keep it as nifty object
    :return: The loaded brain (format depends on the above flag)
    """
    nii_img = nib.load(src_path)
    if as_array:
        return nii_img.get_data()
    else:
        return nii_img


def load_from_folder(src_folder, x_scaling_factor, y_scaling_factor, name_filter='', load_parallel=False):
    """
    Load a brain from a folder. All tiff files will be read sorted and assumed to belong to the same sample.
    Optionally a name_filter string can be supplied which will have to be present in the file names for them
    to be considered part of the sample

    :param str src_folder:
    :param float x_scaling_factor: The scaling of the brain along the x dimension (applied on loading before return)
    :param float y_scaling_factor: The scaling of the brain along the y dimension (applied on loading before return)
    :param str name_filter: will have to be present in the file names for them\
    to be considered part of the sample
    :param bool load_parallel: Use multiprocessing to speedup image loading
    :return: The loaded and scaled brain
    :rtype: np.ndarray
    """
    paths = [os.path.join(src_folder, fname) for fname in sorted(os.listdir(src_folder)) if name_filter in fname]
    loading_function = threaded_load_from_sequence if load_parallel else load_from_paths_sequence
    return loading_function(paths, x_scaling_factor, y_scaling_factor)


def load_img_sequence(img_sequence_file_path, x_scaling_factor, y_scaling_factor, load_parallel=False):
    """
    Load a brain from a sequence of files specified in a text file containing an ordered list of paths

    :param str img_sequence_file_path: The path to the file containing the ordered list of image paths (one per line)
    :param float x_scaling_factor: The scaling of the brain along the x dimension (applied on loading before return)
    :param float y_scaling_factor: The scaling of the brain along the y dimension (applied on loading before return)
    :param bool load_parallel: Use multiprocessing to speedup image loading
    :return: The loaded and scaled brain
    :rtype: np.ndarray
    """
    with open(img_sequence_file_path, 'r') as in_file:
        paths = in_file.readlines()
        paths = [p.strip() for p in paths]
    loading_function = threaded_load_from_sequence if load_parallel else load_from_paths_sequence
    return loading_function(paths, x_scaling_factor, y_scaling_factor)


def threaded_load_from_sequence(paths_sequence, x_scaling_factor=1.0, y_scaling_factor=1.0):
    """
    Use multiprocessing to load a brain from a sequence of image paths.
    Currently the number of parallel processes will be number_of_machine_cores - 1 to leave free
    resources for other tasks on the system. In the future, this might become an argument to the function.

    :param list paths_sequence: The sorted list of the planes paths on the filesystem
    :param float x_scaling_factor: The scaling of the brain along the x dimension (applied on loading before return)
    :param float y_scaling_factor: The scaling of the brain along the y dimension (applied on loading before return)
    :return: The loaded and scaled brain
    :rtype: np.ndarray
    """
    stacks = []
    n_free_cpus_min = 1  # TODO: set as option
    n_processes = mp.cpu_count() - n_free_cpus_min
    pool = ProcessPoolExecutor(max_workers=n_processes)  # FIXME: will not work with interactive interpreter.
    # FIXME: should detect and switch to other method

    n_paths_per_subsequence = math.floor(len(paths_sequence) / n_processes)
    for i in range(n_processes):
        start_idx = i * n_paths_per_subsequence
        end_idx = start_idx + n_paths_per_subsequence
        end_idx = end_idx if end_idx < len(paths_sequence) else -1
        sub_paths = paths_sequence[start_idx:end_idx]

        process = pool.submit(load_from_paths_sequence, sub_paths, x_scaling_factor, y_scaling_factor)
        stacks.append(process)
    stack = np.dstack((s.result() for s in stacks))
    return stack


def load_from_paths_sequence(paths_sequence, x_scaling_factor=1.0, y_scaling_factor=1.0):  # OPTIMISE: load threaded and process by batch
    """
    A single core version of the function to load a brain from a sequence of image paths.

    :param list paths_sequence: The sorted list of the planes paths on the filesystem
    :param float x_scaling_factor: The scaling of the brain along the x dimension (applied on loading before return)
    :param float y_scaling_factor: The scaling of the brain along the y dimension (applied on loading before return)
    :return: The loaded and scaled brain
    :rtype: np.ndarray
    """
    for i, p in enumerate(tqdm(paths_sequence, desc='Loading images', unit='plane')):
        img = tifffile.imread(p)
        if i == 0:
            check_mem(img.nbytes * x_scaling_factor * y_scaling_factor, len(paths_sequence))
            volume = np.empty((int(round(img.shape[0] * x_scaling_factor)),
                               int(round(img.shape[1] * y_scaling_factor)),  # TEST: add test case for shape rounding
                               len(paths_sequence)),
                              dtype=img.dtype)
        if x_scaling_factor != 1 and y_scaling_factor != 1:
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                img = transform.rescale(img,
                                        (x_scaling_factor, y_scaling_factor), mode='constant',
                                        preserve_range=True)
        volume[:, :, i] = img
    return volume


# ######################## OUTPUT METHODS ########################
def to_nii(img, dest_path, scale=(1, 1, 1), affine_transform=None):  # TODO: see if we want also real units scale
    """
    Write the brain volume to disk as nifty image.

    :param img: A nifty image object or numpy array brain
    :param str dest_path: The path where to save the brain.
    :param tuple scale: A tuple of floats to indicate the 'zooms' of the nifty image
    :param np.ndarray affine_transform: A matrix indicating the transform to save in the metadata of the image
    :return:
    """
    if affine_transform is None:
        affine_transform = np.eye(4)
    if not isinstance(img, nib.Nifti1Image):
        img = nib.Nifti1Image(img, affine_transform)
    if scale != (1, 1, 1):  # FIXME: do only if img.get_zomms() is (1, 1, 1) and scale is not
        img.header.set_zooms(scale)
    nib.save(img, dest_path)


def tiff_to_nii(src_path, dest_path):
    """
    Load the tiff image and save it as a nifty image.

    :param str src_path: The path of the tiff image (can be multiple plains (folder of files list) or a single stack
    :param str dest_path: The path to save the nifty image to.
    :return:
    """
    if not dest_path.endswith('.nii.gz'):
        raise ValueError('Path is expected to end in "nii.gz", got {} instead.'.format(dest_path))

    img = load_any(src_path)
    if not isinstance(img, nib.Nifti1Image):
        img = nib.Nifti1Image(img, np.eye(4))
    nib.save(img, os.path.normpath(dest_path))


def nii_to_tiff(src_path, dest_path):
    """
    Load a nifty image and save it as a single tiff stack

    :param str src_path: The path of the source nifty image to load
    :param str dest_path: The path to save the tiff stack to
    :return:
    """
    img = load_nii(src_path, as_array=True)
    tifffile.imsave(dest_path, img)


def to_tiff(img_volume, dest_path):
    """
    Saves the image volume (numpy array) to a tiff stack

    :param np.ndarray img_volume: The image to be saved
    :param dest_path: Where to save the tiff stack
    :return:
    """
    tifffile.imsave(dest_path, img_volume)


def to_tiffs(img_volume, path_prefix, path_suffix='', pad_width=4):
    """
    Save the image volume (numpy array) as a sequence of tiff planes.
    Each plane will have a filepath of the following for:
    pathprefix_zeroPaddedIndex_suffix.tif

    :param np.ndarray img_volume: The image to be saved
    :param str path_prefix:  The prefix for each plane
    :param str path_suffix: The suffix for each plane
    :param int pad_width: The number of digits on which the index of the image (z plane number) will be padded
    :return:
    """
    z_size = img_volume.shape[-1]
    if z_size > 10**pad_width:
        raise ValueError("Not enough padding digits {} for value {}".format(pad_width, z_size))
    for i in range(z_size):
        img = img_volume[:, :, i]
        dest_path = '{}_{}{}.tif'.format(path_prefix, str(i).zfill(pad_width), path_suffix)
        tifffile.imsave(dest_path, img)
