from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import os

from brain_processor import BrainProcessor
from brain_registration import BrainRegistration


def process(_args):
    sample_name = _args.sample_name
    brain = BrainProcessor(args.target_brain, args.output_folder, _args.x_pix_mm, _args.y_pix_mm, _args.z_pix_mm)
    target_brain_path = os.path.join(args.output_folder, '{}_downsampled_filtered.nii'.format(sample_name))
    brain.save(target_brain_path)
    brain_reg = BrainRegistration(sample_name, target_brain_path, args.output_folder)  # TODO: check
    brain_reg.register_affine()  # TODO: have it as option
    brain_reg.register_freeform()
    brain_reg.segment()
    return brain_reg.registered_atlas_img_path


if __name__ == '__main__':
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    # FIXME: add options for all replacing default params and load params from config
    parser.add_argument('sample-name', dest='sample_name', type=str, help='Name of the sample')
    parser.add_argument('output-folder', dest='output_folder', type=str,
                        help='The folder in which to save all the temporary '
                             'and final output of the registration process')
    parser.add_argument('-x', '--x-pixel-mm', dest='x_pixel_mm', type=float, default=0.001,
                        help='Pixel size of the data in the first dimension.'
                             'Warning, for compatibility with the Nifty format'
                             'the value must be specified in mm.')
    parser.add_argument('-y', '--y-pixel-mm', dest='y_pixel_mm', type=float, default=0.001,
                        help='Pixel size of the data in the second dimension.'
                             'Warning, for compatibility with the Nifty format'
                             'the value must be specified in mm.')
    parser.add_argument('-z', '--z-pixel-mm', dest='z_pixel_mm', type=float, default=0.005,
                        help='Pixel size of the data in the third dimension.'
                             'Warning, for compatibility with the Nifty format'
                             'the value must be specified in mm.')

    args = parser.parse_args()

    print("Segmentation finished. Result can be found here: {}".format(process(args)))
