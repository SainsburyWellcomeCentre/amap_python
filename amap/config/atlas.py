import os
from amap.config.config import config_obj

atlas_conf = config_obj['atlas']


def get_atlas_path():
    """
    Get the path to the reference atlas

    :return: The atlas path
    :rtype: str
    """
    return get_atlas_element_path_or_default('atlas_path')


def get_atlas_pixel_sizes_from_config():
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


def get_atlas_element_path(config_entry_name):
    """
    Get the path to an 'element' of the atlas (i.e. the average brain, the atlas, or the hemispheres atlas)

    :param str config_entry_name: The name of the item to retrieve
    :return: The path to that atlas element on the filesystem
    :rtype: str
    """
    atlas_folder_name = os.path.expanduser(atlas_conf['base_folder'])
    atlas_element_filename = atlas_conf[config_entry_name]
    return os.path.abspath(os.path.normpath(os.path.join(atlas_folder_name, atlas_element_filename)))


def get_atlas_element_path_or_default(config_entry_name):
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
        return get_atlas_element_path('default_{}'.format(config_entry_name.replace('path', 'name')))
