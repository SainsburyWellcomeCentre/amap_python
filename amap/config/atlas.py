import os

import numpy as np

from amap.config.config import config_obj
import amap.brain.brain_io as bio

atlas_conf = config_obj['atlas']


class AtlasError(Exception):
    pass


class Atlas(object):
    """
    A class to handle all the atlas data (including the
    """
    def __init__(self, dest_folder='', src_folder=''):
        self.dest_folder = dest_folder
        if src_folder:  # FIXME: hacky
            atlas_conf['base_folder'] = src_folder
        self.src_folder = src_folder

        self._pix_sizes = None  # cached to avoid reloading atlas

        self._data = None
        self._brain_data = None
        self._hemispheres_data = None

        self.original_orientation = atlas_conf['orientation']
        if self.original_orientation != 'horizontal':
            raise NotImplementedError('Unknown orientation {}. Only horizontal supported so far'
                                      .format(self.original_orientation))
    # TODO: put functions below as methods of class

    @property
    def pix_sizes(self):
        """
        Get the dictionary of x, y, z from the after loading it or if the atlas size is default,
        use the values from the config file

        :return: The dictionary of x, y, z pixel sizes
        """
        if self._pix_sizes is None:
            pixel_sizes = self.get_data().header.get_zooms()
            if pixel_sizes != (0, 0, 0):
                self._pix_sizes = {axis: size for axis, size in zip(('x', 'y', 'z'), pixel_sizes)}
            else:
                self._pix_sizes = self.get_pixel_sizes_from_config()
        return self._pix_sizes

    def get_path(self):
        """
        Get the path to the reference atlas

        :return: The atlas path
        :rtype: str
        """
        return self.get_atlas_element_path_or_default('atlas_path')

    def get_brain_path(self):
        return self.get_atlas_element_path_or_default('brain_path')

    def get_hemispheres_path(self):
        return self.get_atlas_element_path_or_default('hemispheres_path')

    def get_default_atlas_path(self):
        return self.get_atlas_element_path('default_atlas_name')

    def get_default_brain_path(self):
        return self.get_atlas_element_path('default_brain_name')

    def get_default_hemispheres_path(self):
        return self.get_atlas_element_path('default_hemispheres_name')

    def get_data(self):
        """
        Load the atlas and return it

        :return: The atlas (nifty image)
        """
        atlas_path = self.get_path()
        if self._data is None:
            self._data = bio.load_nii(atlas_path)
        return self._data

    def load_all(self):
        if self._data is None:
            self._data = bio.load_nii(self.get_path())
        if self._brain_data is None:
            self._brain_data = bio.load_nii(self.get_brain_path())
        if self._hemispheres_data is None:
            self._hemispheres_data = bio.load_nii(self.get_hemispheres_path())

    def save_all(self):
        bio.to_nii(self._data, self.get_dest_path('atlas'))
        bio.to_nii(self._brain_data, self.get_dest_path('brain'))
        bio.to_nii(self._hemispheres_data, self.get_dest_path('hemispheres'))

    def flip(self, axes):
        for axis_idx, flip_axis in enumerate(axes):
            if flip_axis:
                for brain in (self._data.get_data(), self._brain_data.get_data(), self._hemispheres_data.get_data()):
                    brain = np.flip(brain, axis_idx)

    def reorientate_to_sample(self, sample_orientation):  # TODO: do using only nifty header
        transpositions = {
            'horizontal': (1, 0, 2),  # FIXME:
            'coronal': (0, 2, 1),
            'sagittal': (2, 1, 0)  # FIXME:
        }
        transposition = transpositions[sample_orientation]
        for brain in (self._data.get_data(), self._brain_data.get_data(), self._hemispheres_data.get_data()):
            brain = np.transpose(brain, transposition)

    def reorientate_to_self(self, sample_orientation):
        transpositions = {
            'horizontal': (1, 0, 2),  # FIXME:
            'coronal': (2, 0, 1),
            'sagittal': (2, 1, 0)  # FIXME:
        }
        transposition = transpositions[sample_orientation]
        for brain in (self._data.get_data(), self._brain_data.get_data(), self._hemispheres_data.get_data()):
            brain = np.transpose(brain, transposition)

    def get_dest_path(self, atlas_element_name):
        if not self.dest_folder:
            raise AtlasError('Could not get destination path. Missing destination folder information')
        return os.path.join(self.dest_folder, atlas_conf['default_{}_name'.format(atlas_element_name)])

    def make_atlas_scale_transformation_matrix(self):
        scale = self.pix_sizes
        transformation_matrix = np.eye(4)
        for i, axis in enumerate(('x', 'y', 'z')):
            transformation_matrix[i, i] = scale[axis]
        return transformation_matrix

    def get_pixel_sizes_from_config(self):
        """
        Get the dictionary of atlas pixel sizes from the config file.
        The dictionary is structured like this:
        {'x': x_pixel_size_in_mm,
         'y': y_pixel_size_in_mm,
         'z': z_pixel_size_in_mm
        }

        :return: the pixel size dictionary
        :rtype: dict
        """
        return atlas_conf['pixel_size']

    def get_atlas_element_path(self, config_entry_name):
        """
        Get the path to an 'element' of the atlas (i.e. the average brain, the atlas, or the hemispheres atlas)

        :param str config_entry_name: The name of the item to retrieve
        :return: The path to that atlas element on the filesystem
        :rtype: str
        """
        atlas_folder_name = os.path.expanduser(atlas_conf['base_folder'])
        atlas_element_filename = atlas_conf[config_entry_name]
        return os.path.abspath(os.path.normpath(os.path.join(atlas_folder_name, atlas_element_filename)))

    def get_atlas_element_path_or_default(self, config_entry_name):
        """
        Get the path to an 'element' of the atlas (i.e. the average brain, the atlas, or the hemispheres atlas).
        If this was not specified in the configuration, returns the default path from the config.

        :param str config_entry_name: The name of the item to retrieve
        :return: The path to that atlas element on the filesystem
        :rtype: str
        """
        full_path = atlas_conf[config_entry_name]
        if full_path:
            return os.path.abspath(os.path.normpath(full_path))
        else:
            return self.get_atlas_element_path('default_{}'.format(config_entry_name.replace('path', 'name')))
