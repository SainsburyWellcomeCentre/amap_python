import os
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import morphology
from tqdm import trange

from amap.brain.brain_io import BrainIo


class BrainProcessor(object):
    def __init__(self, target_brain_path, output_folder, x_pix_mm, y_pix_mm, z_pix_mm):
        self.target_brain_path = target_brain_path

        atlas_pixel_sizes = self.get_atlas_pix_sizes()
        target_brain = BrainIo.load_any(self.target_brain_path, x_scaling, y_scaling, z_scaling)
        self.target_brain = self.filter_for_registration(target_brain)
        x_scaling = x_pix_mm / atlas_pixel_sizes['x']  # TODO: compute from atlas brain (FIXME: round to some level)
        y_scaling = y_pix_mm / atlas_pixel_sizes['y']
        z_scaling = z_pix_mm / atlas_pixel_sizes['z']
        self.output_folder = output_folder

    def filter(self):
        br = BrainProcessor.filter_for_registration(self.target_brain)
        self.target_brain = np.flip(np.transpose(br, (1, 2, 0)), 2)  # OPTIMISE: see if way to specify in the nii transform instead

    @staticmethod
    def get_atlas_pix_sizes():
        from amap.config.config import config_obj
        config_atlas_path = config_obj['atlas']['path']
        if config_atlas_path:
            atlas_path = config_atlas_path
        else:
            atlas_path = os.path.join(*config_obj['atlas']['default_path'])
        atlas = bio.load_nii(atlas_path)
        pixel_sizes = atlas.header.get_zooms()
        if pixel_sizes != (0, 0, 0):
            return {axis: size for axis, size in zip(('x', 'y', 'z'), pixel_sizes)}
        else:
            return config_obj['atlas']['pixel_size']

    @staticmethod
    def filter_for_registration(brain):
        """
        From Alex Brown

        :return:
        """
        brain = brain.astype(np.float64, copy=False)
        for i in trange(brain.shape[-1], desc='filtering'):
            brain[..., i] = filter_plane_for_registration(brain[..., i])  # OPTIMISE: see if in place better
        brain = scale_to_16_bits(brain)
        brain = brain.astype(np.uint16, copy=False)
        return brain

    def save(self, dest_path):
        atlas_pix_sizes = self.get_atlas_pix_sizes()
        bio.to_nii(self.target_brain, dest_path,
                   scale=(atlas_pix_sizes['x'], atlas_pix_sizes['y'], atlas_pix_sizes['z']),
                   affine_transform=np.eye(4)*0.01)


def filter_plane_for_registration(img_plane):
    img_plane = despeckle_by_opening(img_plane)
    img_plane = pseudo_flatfield(img_plane)
    return img_plane


def pseudo_flatfield(img_plane, sigma=5, size=15):  # FIXME: not using param
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
