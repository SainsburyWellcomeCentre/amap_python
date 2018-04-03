import os, sys, platform
from configobj import ConfigObj


class AmapConfigError(Exception):
    pass


user_config_dir = os.path.join(os.path.expanduser('~'), '.amap')
global_config_directory = os.path.join(sys.prefix, 'etc', 'amap')
shared_directory = os.path.join(sys.prefix, 'share', 'amap')  # Where resources should go

conf_file_name = 'amap.conf'

# The config will be read with this priority
config_dirs = [
    user_config_dir,
    global_config_directory,
    '../amap/config',
    'amap/config',  # WARNING: relies on working directory and uses hard coded sep
    'config',  # For sphinx doc  # TODO: add check that run by sphinx
]
config_dirs = [os.path.normpath(d) for d in config_dirs]
config_paths = [os.path.abspath(os.path.join(d, conf_file_name)) for d in config_dirs]

config_path = None
for p in config_paths:
    if not os.path.exists(p):
        continue
    else:
        config_path = p
        break

if not config_path:
    raise AmapConfigError('Missing config file.\n'
                          ' Tried {}.\n'
                          ' Working directory: {}'.
                          format(config_paths,
                                 os.getcwd()))
config_obj = ConfigObj(config_path, encoding="UTF8", indent_type='    ', unrepr=True)
config_obj.reload()

__os_folder_names = {
    'Linux': 'linux_x64',
    'Darwin': 'osX',
    'Windows': 'win64'
}

try:
    os_folder_name = __os_folder_names[platform.system()]
except KeyError:
    raise ValueError('Platform {} is not recognised as a valid platform. Valid platforms are : {}'.
                     format(platform.system(), __os_folder_names.keys()))


def get_binary(binaries_folder, program_name):
    from pkg_resources import resource_filename, Requirement
    path = "{}/{}/{}".format(binaries_folder, os_folder_name, program_name)
    return resource_filename(Requirement.parse("amap"), path)
