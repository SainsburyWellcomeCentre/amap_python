import os
import sys

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

import numpy as np
from amap.brain.brain_processor import BrainProcessor  # Warning: required to allow direct or indirect import
from amap.registration.brain_registration import BrainRegistration  # Warning: required to allow direct or indirect import


def get_parser():
    """
    Get the argparse argument parser for the application

    :return: The argument parser
    """
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('target_brain_path', metavar='target-brain-path', type=str,
                        help='The path to the brain to analyse')
    parser.add_argument('sample_name', metavar='sample-name', type=str,
                        help='The name of the sample to be used for new files')
    parser.add_argument('output_folder', metavar='output-folder', type=str,
                        help='The folder in which to save all the temporary '
                             'and final output of the registration process')

    parser.add_argument('--sort-input-file', dest='sort_input_file', action='store_true',
                        help='If set to true, the input text file will be sorted using natural sorting.'
                             'This means that the file paths will be sorted as would be expected by a human and'
                             'not purely alphabetically')
    parser.add_argument('--load-parallel', dest='load_parallel', action='store_true',
                        help='Whether to use multiprocessing to load the original image. Useful if stored '
                             'as a sequence of tiff files.')
    parser.add_argument('-p', '--preprocess', action='store_true',
                        help='Whether the target brain needs to be preprocessed (downsampled/filtered) or not')
    parser.add_argument('-s', '--preprocessed-suffix', dest='preprocessed_suffix', type=str,
                        default='downsampled_filtered',
                        help='The suffix to append to the name of the image after preprocessing '
                             '(downsampling and filtering)')

    parser.add_argument('-x', '--x-pixel-mm', dest='x_pixel_mm', type=float, default=0.001,
                        help='Pixel spacing of the data in the first dimension.'
                             'Warning, for compatibility with the Nifty format'
                             'the value must be specified in mm.')
    parser.add_argument('-y', '--y-pixel-mm', dest='y_pixel_mm', type=float, default=0.001,
                        help='Pixel spacing of the data in the second dimension.'
                             'Warning, for compatibility with the Nifty format'
                             'the value must be specified in mm.')
    parser.add_argument('-z', '--z-pixel-mm', dest='z_pixel_mm', type=float, default=0.005,
                        help='Pixel spacing of the data in the third dimension.'
                             'Warning, for compatibility with the Nifty format'
                             'the value must be specified in mm.')
    parser.add_argument('-o', '--orientation', type=str, choices=('coronal', 'sagittal', 'horizontal'),
                        default='coronal',
                        help='The orientation of the sample brain. This is used to transpose the atlas'
                             'into the same orientation as the brain.')
    parser.add_argument('--flip-x', dest='flip_x', action='store_true',
                        help='Whether to flip the sample brain along the first dimension.')  # Warning: atlas reference
    parser.add_argument('--flip-y', dest='flip_y', action='store_true',
                        help='Whether to flip the sample brain along the second dimension.')
    parser.add_argument('--flip-z', dest='flip_z', action='store_true',
                        help='Whether to flip the sample brain along the third dimension.')

    parser.add_argument('--save-unfiltered', dest='save_unfiltered', action='store_true',
                        help='Save the brain before filtering (only downsampled). This is useful for'
                             'visualising the results.')
    parser.add_argument('--left-right', dest='left_right', action='store_true',
                        help='Whether to do register the hemispheres (left/right) atlas too to get informations'
                             'about lateralisation.')
    parser.add_argument('--generate-outlines', dest='generate_outlines', action='store_true',
                        help='Generate the color boundaries of the mask in the sample reference space. This '
                             'is useful for testing the output.')

    parser.add_argument('--erase-intermediate-files', dest='erase_intermediate_files', action='store_true',
                        help='Whether the program should erase the intermediate image volumes used by niftyreg after'
                             'the program finished successfully. Use this only if you know what you are doing.')
    parser.add_argument('--delete-logs', dest='delete_logs', action='store_true',
                        help='Delete the logs generated by NiftyReg. Use this only if you know what you are doing.')

    parser.add_argument('-r', '--register', action='store_true', help='Register the atlas to the sample.'  # FIXME: transform to skip registration
                                                                      '(affine and freeform)')
    parser.add_argument('--atlas-mask-planes', dest='atlas_mask_planes', type=int, nargs=2, default=(0, -1),
                        help='The START and END of the range of planes to keep for the registration.'
                             'The planes before START and after END will be masked. It defaults to the whole range'
                             'meaning nothing will be masked.')

    return parser


def delete_intermediate_files(_args):
    """
    Deletes temporary file on the drive that are generated by nifty_reg steps but may not be
    useful

    :param argparse.Namespace _args:
    :return:
    """
    files_to_delete = ('downsampled_filtered.nii',
                       'affine_registered_atlas_brain.nii',
                       'freeform_registered_atlas_brain.nii')
    for intermediate_file_basename in files_to_delete:
        intermediate_file_path = os.path.join(_args.output_folder,
                                              '{}_{}'.format(_args.sample_name, intermediate_file_basename))
        os.remove(intermediate_file_path)


def delete_logs(_args, log_names):
    """
    Delete all logs from log_names

    :param argparse.Namespace _args:
    :param tuple log_names:
    :return:
    """
    for log_name in log_names:
        log_path = os.path.join(_args.output_folder, '{}_{}'.format(_args.sample_name, log_name))
        os.remove(log_path)


def delete_error_logs(_args):
    """
    Delete all the error log files generated by the calls to the different binaries of nifty_Reg

    :param _args:
    :return:
    """
    delete_logs(_args, ('affine.err', 'freeform.err', 'segment.err'))


def delete_regular_logs(_args):
    """
    Delete all the regular log files generated by the calls to the different binaries of nifty_Reg

    :param _args:
    :return:
    """
    delete_logs(_args, ('affine.log', 'freeform.log', 'segment.log'))


def process(_args):
    """
    The main function that will perform the library calls and register the atlas to the brain given on the CLI

    :param _args:
    :return: The path to the registered atlas
    :rtype: str
    """
    sample_name = _args.sample_name
    if not os.path.exists(_args.output_folder):
        result = input("Output folder does not exist, would you like to create it. [Y/n]")
        if result.lower() in ('Y', 'Yes', 'yes', 'y', ''):  # TEST:
            os.makedirs(_args.output_folder)
        else:
            sys.exit('Missing output folder, aborting')
    if _args.preprocess:
        print("Preprocessing")
        brain = BrainProcessor(_args.target_brain_path, _args.output_folder,
                               _args.x_pixel_mm, _args.y_pixel_mm, _args.z_pixel_mm,
                               original_orientation=_args.orientation,
                               load_parallel=_args.load_parallel,
                               sort_input_file=_args.sort_input_file)
        brain.swap_atlas_orientation_to_self()
        brain.flip_atlas((_args.flip_x, _args.flip_y, _args.flip_z))  # TEST: check that axes match
        brain.atlas.save_all()
        if _args.save_unfiltered:
            downsampled_brain_path = os.path.join(_args.output_folder, '{}_{}.nii'
                                                  .format(sample_name, 'downsampled'))  # FIXME: extract
            brain.target_brain = brain.target_brain.astype(np.uint16, copy=False)  # FIXME: avaoid hardcoding unless io
            brain.save(downsampled_brain_path)
        brain.filter()
        filtered_brain_path = os.path.join(_args.output_folder,
                                           '{}_{}.nii'.format(sample_name, _args.preprocessed_suffix))
        brain.save(filtered_brain_path)
    else:
        filtered_brain_path = _args.target_brain_path
    brain_reg = BrainRegistration(sample_name, filtered_brain_path, _args.output_folder,
                                  atlas_start_slice=_args.atlas_mask_planes[0],
                                  atlas_end_slice=_args.atlas_mask_planes[1])
    if _args.register:
        print("Registering")
        print("\tStarting affine registration")
        brain_reg.register_affine()  # TODO: have it as option
        print("\tStarting freeform registration")
        brain_reg.register_freeform()

        print("\tStarting segmentation")
        brain_reg.segment()
        if _args.left_right:
            print("\tSegmenting hemispheres")
            brain_reg.register_hemispheres()
        if _args.generate_outlines:
            print("\tGenerating outlines")
            brain_reg.generate_outlines()
    print("Done")
    return brain_reg.registered_atlas_img_path


def main():
    args = get_parser().parse_args()
    results_path = process(args)

    print("Segmentation finished. Results can be found here: {}".format(results_path))
    if args.erase_intermediate_files:
        delete_error_logs(args)
        delete_intermediate_files(args)
    if args.delete_logs:
        delete_regular_logs(args)


if __name__ == '__main__':
    cwd = os.path.abspath('.')
    sys.path.insert(0, cwd)

    from amap.brain.brain_processor import BrainProcessor
    from amap.registration.brain_registration import BrainRegistration
    main()
