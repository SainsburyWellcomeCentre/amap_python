"""
brain_processor
===============

A module to prepare brains for registration
"""
import numpy as np

from scipy.ndimage import gaussian_filter
from skimage import morphology
from tqdm import trange

from amap.brain import brain_io as bio
from amap.config.atlas import make_atlas_scale_transformation_matrix, get_atlas_pix_sizes


class BrainProcessor(object):
    """
    A class to do some basic processing to the brains (3D image scans) including

    - Changing the orientation
    - filtering using despeckle and pseudo flatfield
    """
    def __init__(self, target_brain_path, output_folder, x_pix_mm, y_pix_mm, z_pix_mm,
                 original_orientation='coronal', load_parallel=False, sort_input_file=False):
        """

        :param str target_brain_path: The path to the brain to be processed (image file, paths file or folder)
        :param str output_folder: The folder where to store the results
        :param float x_pix_mm: The pixel spacing in the x dimension. It is used to scale the brain to the atlas.
        :param float y_pix_mm: The pixel spacing in the x dimension. It is used to scale the brain to the atlas.
        :param float z_pix_mm: The pixel spacing in the x dimension. It is used to scale the brain to the atlas.
        :param str original_orientation:
        :param bool load_parallel: Load planes in parallel using multiprocessing for faster data loading
        :param bool sort_input_file: If set to true and the input is a filepaths file, it will be naturally sorted
        """
        self.target_brain_path = target_brain_path

        atlas_pixel_sizes = get_atlas_pix_sizes()
        x_scaling = x_pix_mm / atlas_pixel_sizes['x']  # FIXME: round to um
        y_scaling = y_pix_mm / atlas_pixel_sizes['y']
        z_scaling = z_pix_mm / atlas_pixel_sizes['z']

        self.original_orientation = original_orientation

        self.target_brain = bio.load_any(self.target_brain_path, x_scaling, y_scaling, z_scaling,
                                         load_parallel=load_parallel, sort_input_file=sort_input_file)
        self.swap_orientation_from_original_to_atlas()
        self.output_folder = output_folder

    def flip(self, axes):
        """
        Flips the brain along the specified axes.

        :param tuple axes: a tuple of 3 booleans indicating which axes to flip or not
        :return:
        """
        for axis_idx, flip_axis in enumerate(axes):
            if flip_axis:
                # print("Flipping axis {}".format('xyz'[axis_idx]))
                self.target_brain = np.flip(self.target_brain, axis_idx)

    def swap_orientation_from_original_to_atlas(self, atlas_orientation='horizontal'):
        """
        Transposes the orientation of the brain from original orientation (an attribute
        of the class) to atlas orientation.
        It uses a table of transpositions for each original orientation and assumes the atlas
        is oriented in the horizontal plane

        :param str atlas_orientation:
        :return:
        """
        if atlas_orientation != 'horizontal':
            raise NotImplementedError('Only supported atlas orientation is horizontal')
        transpositions = {
            'horizontal': (1, 0, 2),
            'coronal': (1, 2, 0),
            'sagittal': (2, 1, 0)
        }
        transposition = transpositions[self.original_orientation]
        self.target_brain = np.transpose(self.target_brain, transposition)

    def swap_orientation_from_atlas_to_original(self, atlas_orientation='horizontal'):
        """
        Transposes the orientation of the brain from atlas orientation to original orientation
        (an attribute of the class).
        It uses a table of transpositions for each original orientation and assumes the atlas
        is oriented in the horizontal plane.

        :param str atlas_orientation:
        :return:
        """
        if atlas_orientation != 'horizontal':
            raise NotImplementedError('Only supported atlas orientation is horizontal')
        transpositions = {
            'horizontal': (1, 0, 2),
            'coronal': (2, 0, 1),
            'sagittal': (2, 1, 0)
        }
        transposition = transpositions[self.original_orientation]
        self.target_brain = np.transpose(self.target_brain, transposition)

    def filter(self):
        """
        Applies a set of filters to the brain to avoid overfitting details in the image during
        registration.

        :return:
        """
        self.swap_orientation_from_atlas_to_original()  # process along original z dimension
        self.target_brain = BrainProcessor.filter_for_registration(self.target_brain)
        self.swap_orientation_from_original_to_atlas()  # reset to atlas orientation

    @staticmethod
    def filter_for_registration(brain):
        """
        A static method to filter a 3D image to allow registration (avoids overfitting details
        in the image) (algorithm from Alex Brown).
        The filter is composed of a despeckle filter using opening and a pseudo flatfield filter

        :return: The filtered brain
        :rtype: np.array
        """
        brain = brain.astype(np.float64, copy=False)
        for i in trange(brain.shape[-1], desc='filtering', unit='plane'):  # OPTIMISE: could multiprocess but not slow
            brain[..., i] = filter_plane_for_registration(brain[..., i])  # OPTIMISE: see if in place better
        brain = scale_to_16_bits(brain)
        brain = brain.astype(np.uint16, copy=False)
        return brain

    def save(self, dest_path):
        """
        Save self.target_brain to dest_path as a nifty image.
        The scale (zooms of the output nifty image) is copied from the atlas brain.

        :param str dest_path:
        :return:
        """
        atlas_pix_sizes = get_atlas_pix_sizes()
        bio.to_nii(self.target_brain, dest_path,
                   scale=(atlas_pix_sizes['x'], atlas_pix_sizes['y'], atlas_pix_sizes['z']),
                   affine_transform=np.eye(4)*0.01)  # FIXME: do not hardcode scale here


def filter_plane_for_registration(img_plane):
    """
    Apply a set of filter to the plane (typically to avoid overfitting details in the image during
    registration)
    The filter is composed of a despeckle filter using opening and a pseudo flatfield filter

    :param np.array img_plane: A 2D array to filter
    :return: The filtered image
    :rtype: np.array
    """
    img_plane = despeckle_by_opening(img_plane)
    img_plane = pseudo_flatfield(img_plane)
    return img_plane


def pseudo_flatfield(img_plane, sigma=5):
    """
    Pseudo flat field filter implementation using a detrending by a heavily gaussian filtered
    copy of the image.

    :param np.array img_plane: The image to filter
    :param int sigma: The sigma of the gaussian filter applied to the image used for detrending
    :return: The pseudo flat field filtered image
    :rtype: np.array
    """
    # TODO: check gausian filter mode (one of {‘reflect’, ‘constant’, ‘nearest’, ‘mirror’, ‘wrap’})
    img_plane = img_plane.copy()  # FIXME: check if necessary
    filtered_img = gaussian_filter(img_plane, sigma)
    return img_plane / (filtered_img + 1)


def scale_to_16_bits(img):
    """
    Normalise the input image to the full 0-2^16 bit depth.

    :param np.array img: The input image
    :return: The normalised image
    :rtype: np.array
    """
    normalised = img / img.max()
    return normalised * (2**16 - 1)


def despeckle_by_opening(img_plane, radius=2):  # WARNING: inplace operation
    """
    Despeckle the image plane using a grayscale opening operation

    :param np.array img_plane:
    :param int radius: The radius of the opening kernel
    :return: The despeckled image
    :rtype: np.array
    """
    kernel = morphology.disk(radius)
    morphology.opening(img_plane, out=img_plane, selem=kernel)
    return img_plane
