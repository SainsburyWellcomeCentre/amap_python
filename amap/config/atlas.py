import os
from amap.config.config import config_obj

atlas_conf = config_obj['atlas']


def get_atlas_path():
    return get_atlas_element_path_or_default('atlas_path')


def get_atlas_pixel_sizes_from_config():
    return atlas_conf['pixel_size']


def get_atlas_element_path(config_entry_name):  # FIXME: same name
    atlas_folder_name = os.path.expanduser(atlas_conf['base_folder'])
    atlas_element_filename = atlas_conf[config_entry_name]
    return os.path.abspath(os.path.normpath(os.path.join(atlas_folder_name, atlas_element_filename)))


def get_atlas_element_path_or_default(config_entry_name):
    full_path = atlas_conf[config_entry_name]
    if full_path:
        return os.path.abspath(os.path.normpath(full_path))
    else:
        return get_atlas_element_path('default_{}'.format(config_entry_name.replace('path', 'name')))
