import os
import sys
cwd = os.path.abspath('.')
sys.path.insert(0, cwd)

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from amap.brain.brain_processor import BrainProcessor
from amap.registration.brain_registration import BrainRegistration


def process(_args):
    sample_name = _args.sample_name
    if _args.preprocess:
        print("Preprocessing")
        brain = BrainProcessor(args.target_brain_path, args.output_folder,
                               _args.x_pixel_mm, _args.y_pixel_mm, _args.z_pixel_mm)
        brain.filter()
        filtered_brain_path = os.path.join(args.output_folder, '{}_{}.nii'.format(sample_name, _args.preprocessed_suffix))
        brain.save(filtered_brain_path)
    else:
        filtered_brain_path = _args.target_brain_path
    print("Registering")
    brain_reg = BrainRegistration(sample_name, filtered_brain_path, args.output_folder)  # TODO: check
    print("\tStarting affine registration")
    brain_reg.register_affine()  # TODO: have it as option
    print("\tStarting freeform registration")
    brain_reg.register_freeform()
    print("\tStarting segmentation")
    brain_reg.segment()
    print("Done")
    return brain_reg.registered_atlas_img_path


def get_parser():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('target_brain_path', metavar='target-brain-path', type=str,
                        help='The path to the brain to analyse')
    parser.add_argument('sample_name', metavar='sample-name', type=str,
                        help='The name of the sample to be used for new files')
    parser.add_argument('output_folder', metavar='output-folder', type=str,
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
    parser.add_argument('-p', '--preprocess', action='store_true',
                        help='Whether the target brain needs to be preprocessed (downsampled/filtered) or not')
    parser.add_argument('-s', '--preprocessed-suffix', dest='preprocessed_suffix', type=str,
                        default='downsampled_filtered',
                        help='The suffix to append to the name of the image after preprocessing '
                             '(downsampling and filtering)')

    return parser.parse_args()


if __name__ == '__main__':
    args = get_parser()

    print("Segmentation finished. Result can be found here: {}".format(process(args)))
