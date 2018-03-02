import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import morphology

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

    def get_atlas_pix_sizes(self):
        from amap.config.config import config
        atlas = BrainIo.load_nii(config['atlas']['path'])
        pixel_sizes = atlas.header.get_zooms()
        if pixel_sizes != (0, 0, 0):
            return {axis: size for axis, size in zip(('x', 'y', 'z'), pixel_sizes)}
        else:
            return config['atlas']['pixel_size']

    def filter_for_registration(self, brain):
        """
        From Alex Brown

        :return:
        """
        brain.astype(np.float64)
        for i in brain.shape[-1]:
            img_plane = brain[..., i]
            img_plane = despeckle_by_erode_dilate(img_plane)
            img_plane = pseudo_flatfield(img_plane)
            brain[..., i] = img_plane
        normalise_to_16_bits(brain)
        brain.astype(np.uint16)
        return brain

    def save(self, dest_path):
        BrainIo.to_nii(self.target_brain, dest_path)


def pseudo_flatfield(img_plane, sigma=5, size=15):
    # TODO: check gausian filter mode (one of {‘reflect’, ‘constant’, ‘nearest’, ‘mirror’, ‘wrap’})
    filtered_img = gaussian_filter(img_plane, sigma)
    return img_plane / (filtered_img + 1)


def normalise_to_16_bits(img):
    return (img / img.max()) * 2**16


def despeckle_by_erode_dilate(img_plane, radius=2):  # WARNING: inplace operation
    kernel = morphology.disk(radius)
    morphology.erosion(img_plane, out=img_plane, selem=kernel)
    morphology.dilation(img_plane, out=img_plane, selem=kernel)
    return img_plane
