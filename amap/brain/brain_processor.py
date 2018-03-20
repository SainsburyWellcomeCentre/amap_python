import os
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import morphology
from tqdm import trange

from amap.brain import brain_io as bio


def get_atlas_pix_sizes():
    atlas, config_obj = load_atlas()
    pixel_sizes = atlas.header.get_zooms()
    if pixel_sizes != (0, 0, 0):
        return {axis: size for axis, size in zip(('x', 'y', 'z'), pixel_sizes)}
    else:
        return config_obj['atlas']['pixel_size']


def load_atlas():
    from amap.config.config import config_obj
    config_atlas_path = config_obj['atlas']['path']
    if config_atlas_path:
        atlas_path = config_atlas_path
    else:
        atlas_path = os.path.join(*config_obj['atlas']['default_path'])
    atlas = bio.load_nii(atlas_path)
    return atlas, config_obj


class BrainProcessor(object):
    def __init__(self, target_brain_path, output_folder, x_pix_mm, y_pix_mm, z_pix_mm,
                 original_orientation='coronal', load_parallel=False):
        self.target_brain_path = target_brain_path

        atlas_pixel_sizes = get_atlas_pix_sizes()
        x_scaling = x_pix_mm / atlas_pixel_sizes['x']  # FIXME: round to um
        y_scaling = y_pix_mm / atlas_pixel_sizes['y']
        z_scaling = z_pix_mm / atlas_pixel_sizes['z']

        self.original_orientation = original_orientation

        self.target_brain = bio.load_any(self.target_brain_path, x_scaling, y_scaling, z_scaling,
                                         load_parallel=load_parallel)
        self.swap_orientation_from_original_to_atlas()
        self.output_folder = output_folder

    def flip(self, axes):
        """

        :param tuple axes: a tuple of 3 booleans indicating which axes to flip or not
        :return:
        """
        for axis_idx, flip_axis in enumerate(axes):
            if flip_axis:
                # print("Flipping axis {}".format('xyz'[axis_idx]))
                self.target_brain = np.flip(self.target_brain, axis_idx)

    def swap_orientation_from_original_to_atlas(self, atlas_orientation='horizontal', flip_z=False):
        if atlas_orientation != 'horizontal':
            raise NotImplementedError('Only supported atlas orientation is horizontal')
        transpositions = {
            'horizontal': (1, 0, 2),
            'coronal': (1, 2, 0),
            'sagittal': (2, 1, 0)
        }
        transposition = transpositions[self.original_orientation]
        self.target_brain = np.transpose(self.target_brain, transposition)

    def swap_orientation_from_atlas_to_original(self, atlas_orientation='horizontal', flip_z=False):
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
        self.swap_orientation_from_atlas_to_original()  # process along original z dimension
        self.target_brain = BrainProcessor.filter_for_registration(self.target_brain)
        self.swap_orientation_from_original_to_atlas()  # reset to atlas orientation

    @staticmethod
    def filter_for_registration(brain):
        """
        From Alex Brown

        :return:
        """
        brain = brain.astype(np.float64, copy=False)
        for i in trange(brain.shape[-1], desc='filtering', unit='plane'):  # OPTIMISE: could multiprocess but not slow
            brain[..., i] = filter_plane_for_registration(brain[..., i])  # OPTIMISE: see if in place better
        brain = scale_to_16_bits(brain)
        brain = brain.astype(np.uint16, copy=False)
        return brain

    def save(self, dest_path):
        atlas_pix_sizes = get_atlas_pix_sizes()
        bio.to_nii(self.target_brain, dest_path,
                   scale=(atlas_pix_sizes['x'], atlas_pix_sizes['y'], atlas_pix_sizes['z']),
                   affine_transform=np.eye(4)*0.01)  # FIXME: do not hardcode scale here


def filter_plane_for_registration(img_plane):
    img_plane = despeckle_by_opening(img_plane)
    img_plane = pseudo_flatfield(img_plane)
    return img_plane


def pseudo_flatfield(img_plane, sigma=5):
    # TODO: check gausian filter mode (one of {‘reflect’, ‘constant’, ‘nearest’, ‘mirror’, ‘wrap’})
    img_plane = img_plane.copy()  # FIXME: check if necessary
    filtered_img = gaussian_filter(img_plane, sigma)
    return img_plane / (filtered_img + 1)


def scale_to_16_bits(img):
    normalised = img / img.max()
    return normalised * (2**16 - 1)


def despeckle_by_opening(img_plane, radius=2):  # WARNING: inplace operation
    kernel = morphology.disk(radius)
    morphology.opening(img_plane, out=img_plane, selem=kernel)
    return img_plane
