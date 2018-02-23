import os, sys, platform
from configobj import ConfigObj


class AmapConfigError(Exception):
    pass


global_config_directory = os.path.join(sys.prefix, 'etc', 'amap')
user_config_dir = os.path.join(os.path.expanduser('~'), '.amap')
shared_directory = os.path.join(sys.prefix, 'share', 'amap')  # Where resources should go

conf_file_name = 'amap.conf'

# The config will be read with this priority
config_dirs = [
    os.path.join(user_config_dir, conf_file_name),
    global_config_directory,
    'config',  # WARNING: relies on working directory
    '../config',  # For sphinx doc  # TODO: add check that run by sphinx
]

config_path = None
for d in config_dirs:
    p = os.path.join(d, conf_file_name)
    if not os.path.exists(p):
        continue
    else:
        config_path = p
        break

if not config_path:
    raise AmapConfigError('Missing config file. Searched {}'.format(config_dirs))
config = ConfigObj(config_path, encoding="UTF8", indent_type='    ', unrepr=True)
config.reload()

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
