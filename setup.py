import os
import sys
import argparse
import shutil
import tarfile
import urllib.request
from setuptools import setup, find_packages
import tempfile


requirements = [
    'psutil',
    'numpy>=1.12',
    'scipy',
    'scikit-image',
    'tifffile',
    'nibabel',
    'tqdm',
    'configobj',
    'natsort'
]


ATLAS_DOWNLOAD_REQUIRED_GB = 1.3
ATLAS_INSTALL_REQUIRED_GB = 20.5
ATLAS_BASE_URL = 'https://www.dropbox.com/s/sjhh9uy7e2ri75u/atlas.tar.bz2?dl={}'
DEFAULT_CONFIG_FOLDER = '~/.amap'


class AtlasInstallError(Exception):
    pass


def download_atlas(atlas_dest_path):
    direct_download = True
    atlas_url = ATLAS_BASE_URL.format(int(direct_download))
    print("Downloading the atlas")
    with urllib.request.urlopen(atlas_url) as response:
        with open(atlas_dest_path, 'wb') as outfile:
            shutil.copyfileobj(response, outfile)


def extract_atlas(atlas_path, atlas_dest_path):
    tar = tarfile.open(atlas_path)
    tar.extractall(path=atlas_dest_path)
    tar.close()


def install_atlas(atlas_download_path, atlas_install_path):  # TODO: check that intermediate folders exist
    if not os.path.exists(os.path.dirname(atlas_download_path)):
        raise AtlasInstallError("Could not find folder {} to download atlas"
                                .format(os.path.dirname(atlas_download_path)))
    if not os.path.exists(atlas_install_path):
        raise AtlasInstallError("Could not find folder {} to install the atlas".format(atlas_install_path))
    if disk_free_gb(os.path.dirname(atlas_download_path)) < ATLAS_DOWNLOAD_REQUIRED_GB:
        raise AtlasInstallError("Insufficient disk space in {} to download atlas"
                                .format(os.path.dirname(atlas_download_path)))
    if disk_free_gb(atlas_install_path) < ATLAS_INSTALL_REQUIRED_GB:
        raise AtlasInstallError("Insufficient disk space in {} to install atlas".format(atlas_install_path))
    download_atlas(atlas_download_path)
    extract_atlas(atlas_download_path, atlas_install_path)
    os.remove(atlas_download_path)


def disk_free_gb(file_path):
    stats = os.statvfs(file_path)
    return (stats.f_frsize * stats.f_bavail) / 1024**3


def amend_cfg(cfg_folder, new_atlas_folder):
    cfg_file_path = os.path.join(cfg_folder, 'amap.conf')
    with open(cfg_file_path, 'r') as in_conf:
        data = in_conf.readlines()
    for i, line in enumerate(data):
        data[i] = line.replace("base_folder = '{}".format(DEFAULT_CONFIG_FOLDER), "base_folder = '{}".format(new_atlas_folder))
    with open(cfg_file_path, 'w') as out_conf:
        out_conf.writelines(data)


def install_cfg(cfg_folder):
    if not os.path.exists(cfg_folder):
        os.makedirs(cfg_folder)
    shutil.copy(os.path.normpath('./amap/config/amap.conf'), cfg_folder)


def fix_path(path):
    """
    Converts the Unix path string to the current platform
    
    :param str path:
    :return: 
    """
    return os.path.abspath(os.path.expanduser(os.path.normpath(path)))


temp_dir = tempfile.TemporaryDirectory()
temp_dir_path = temp_dir.name
parser = argparse.ArgumentParser(argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('--install-atlas', dest='install_atlas', action='store_true',
                    help='Automatically download and install the atlas')
parser.add_argument('--atlas-install-path', dest='atlas_install_path', type=str,
                    default=DEFAULT_CONFIG_FOLDER,
                    help='The path to install the atlas to. (Requires 20GB disk space).')
parser.add_argument('--atlas-download-path', dest='atlas_download_path', type=str,
                    default=os.path.join(temp_dir_path, 'atlas.tar.bz2'),
                    help='The path to donwload the atlas into. (Requires 1.2GB disk space).')
parser.add_argument('--dev-mode', dest='dev_mode', action='store_true',
                    help='Whether to download the dependencies for developing amap.')
parser.add_argument('--amap-config-folder', dest='amap_config_folder', type=str,
                    default=DEFAULT_CONFIG_FOLDER,
                    help='The location to store the amap config file.')
args, setuptools_args = parser.parse_known_args()
sys.argv = sys.argv[:1] + setuptools_args  # Strip these arguments from sys.argv for setuptools

args.atlas_install_path = fix_path(args.atlas_install_path)
args.atlas_download_path = fix_path(args.atlas_download_path)
args.amap_config_folder = fix_path(args.amap_config_folder)
if args.dev_mode:
    requirements.append('pytest')
install_cfg(args.amap_config_folder)
if args.install_atlas:
    install_atlas(args.atlas_download_path, args.atlas_install_path)
    amend_cfg(args.atlas_install_path, args.amap_config_folder)


setup(
    name='amap',
    version='1.0.0',
    packages=find_packages(exclude=('doc', 'tests*')),
    install_requires=requirements,
    url='',
    license='',
    author='Christian Niedworok and Charly Rousseau',
    author_email='',
    description='aMAP is a tool for optimized automated mouse atlas propagation '
                'based on clinical registration software (NiftyReg) for anatomical segmentation '
                'of high-resolution 3D fluorescence images of the adult mouse brain.',
    classifiers=[
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: Science/Research'
    ],
    include_package_data=True,
    package_data={
        '': ['bin/nifty_reg/linux_x64/reg_*', 'bin/nifty_reg/osX/reg_*'],
    },
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'amap = amap.main:main'
        ]
    }
)
