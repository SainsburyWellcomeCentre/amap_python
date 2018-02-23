import os
import numpy as np
import psutil
from skimage import transform
import tifffile
import nibabel as nib


class BrainIoLoadException(Exception):
    pass


class BrainIo(object):

    @staticmethod
    def check_mem(img_byte_size, n_imgs):
        total_size = img_byte_size * n_imgs
        free_mem = psutil.virtual_memory().available
        if total_size >= free_mem:
            raise BrainIoLoadException('Not enough memory on the system to complete loading operation'
                                       'Needed {}, only {} available.'.format(total_size, free_mem))

    # ######################## INPUT METHODS ####################
    @staticmethod
    def load_from_paths_sequence(paths_sequence, x_scaling_factor=1.0, y_scaling_factor=1.0):
        imgs = []
        for p in paths_sequence:
            img = tifffile.imread(p)
            if not imgs:
                BrainIo.check_mem(img.nbytes, len(paths_sequence))
            if x_scaling_factor != 1 and y_scaling_factor != 1:
                # FIXME: see if needs filter with missing anti_aliasing
                img = transform.rescale(img,
                                        (x_scaling_factor, y_scaling_factor),
                                        anti_aliasing=True, preserve_range=True)  # TEST:
            # TODO: see transform.pyramid_reduce
        imgs.append(img)
        volume = np.array(imgs)
        return volume

    @staticmethod
    def load_img_sequence(img_sequence_file, x_scaling_factor, y_scaling_factor):
        with open(img_sequence_file, 'r') as in_file:
            paths = in_file.readlines()
            paths = [p.strip() for p in paths]
        return BrainIo.load_from_paths_sequence(paths, x_scaling_factor, y_scaling_factor)

    @staticmethod
    def load_from_folder(src_folder, x_scaling_factor, y_scaling_factor, name_filter=''):
        paths = [os.path.join(src_folder, fname) for fname in os.listdir(src_folder) if name_filter in fname]
        return BrainIo.load_from_paths_sequence(paths, x_scaling_factor, y_scaling_factor)

    @staticmethod
    def load_nii(src_path):
        return nib.load(src_path)

    @staticmethod
    def load_img_stack(stack_path):
        stack = tifffile.imread(stack_path)
        return stack

    @staticmethod
    def load_any(src_path, x_scaling_factor=1.0, y_scaling_factor=1.0, z_scaling_factor=1.0):
        """
        .. warning:: x and y scaling not used at the moment if loading a complete image

        :param src_path:
        :param x_scaling_factor:
        :param y_scaling_factor:
        :param z_scaling_factor:
        :return:
        """
        if os.path.isdir(src_path):
            img = BrainIo.load_from_folder(src_path, x_scaling_factor, y_scaling_factor, name_filter='.tif')
        elif src_path.endswith('.txt'):
            img = BrainIo.load_img_sequence(src_path, x_scaling_factor, y_scaling_factor)
        elif src_path.endswith('.tif'):
            img = BrainIo.load_img_stack(src_path)
        elif src_path.endswith(('.nii', '.nii.gz')):
            img = BrainIo.load_nii(src_path)
        else:
            raise NotImplementedError('Could not guess loading method for path {}'.format(src_path))
        if z_scaling_factor != 1:
            img = transform.rescale(img, (1, 1, z_scaling_factor))
        return img

    # ######################## OUTPUT METHODS ########################
    @staticmethod
    def to_tiffs(img_volume, path_prefix, path_suffix=''):
        for i in range(img_volume.shape[-1]):
            img = img_volume[::i]
            dest_path = '{}_{}{}.tif'.format(path_prefix, i, path_suffix)
            tifffile.imsave(dest_path, img)

    @staticmethod
    def nii_to_tiff(src_path, dest_path):
        nii_img = BrainIo.load_nii(src_path)
        img = nii_img.data()
        tifffile.imsave(dest_path, img)

    @staticmethod
    def tiff_to_nii(src_path, dest_path):
        if not dest_path.endswith('.nii.gz'):
            raise ValueError('Path is expected to end in "nii.gz", got {} instead.'.format(dest_path))

        img = BrainIo.load_any(src_path)
        nib.save(img, os.path.join(dest_path))  # FIXME: why os.path.join

    @staticmethod
    def to_nii(img, dest_path):
        nib.save(img, dest_path)
