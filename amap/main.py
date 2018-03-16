import os
import sys
cwd = os.path.abspath('.')
sys.path.insert(0, cwd)

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from amap.brain.brain_processor import BrainProcessor
from amap.registration.brain_registration import BrainRegistration


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
    parser.add_argument('--save-unfiltered', dest='save_unfiltered', action='store_true',
                        help='Save the brain before filtering (only downsampled). This is useful for'
                             'visualising the results.')
    parser.add_argument('--erase-intermediate-files', dest='erase_intermediate_files', action='store_true',
                        help='Whether the program should erase the intermediate image volumes used by niftyreg after'
                             'the program finished successfully. Use this only if you know what you are doing.')
    parser.add_argument('--delete-logs', dest='delete_logs', action='store_true',
                        help='Delete the logs generated by NiftyReg. Use this only if you know what you are doing.')
    parser.add_argument('-p', '--preprocess', action='store_true',
                        help='Whether the target brain needs to be preprocessed (downsampled/filtered) or not')
    parser.add_argument('-s', '--preprocessed-suffix', dest='preprocessed_suffix', type=str,
                        default='downsampled_filtered',
                        help='The suffix to append to the name of the image after preprocessing '
                             '(downsampling and filtering)')

    return parser.parse_args()


def delete_intermediate_files(_args):
    files_to_delete = ('downsampled_filtered.nii',
                       'affine_registered_atlas_brain.nii',
                       'freeform_registered_atlas_brain.nii')
    for intermediate_file_basename in files_to_delete:
        intermediate_file_path = os.path.join(_args.output_folder,
                                              '{}_{}'.format(_args.sample_name, intermediate_file_basename))
        os.remove(intermediate_file_path)


def delete_logs(_args, log_names):
    for log_name in log_names:
        log_path = os.path.join(_args.output_folder, '{}_{}'.format(_args.sample_name, log_name))
        os.remove(log_path)


def delete_error_logs(_args):
    delete_logs(_args, ('affine.err', 'freeform.err', 'segment.err'))


def delete_regular_logs(_args):
    delete_logs(_args, ('affine.err', 'freeform.err', 'segment.err'))


def process(_args):
    sample_name = _args.sample_name
    if _args.preprocess:
        print("Preprocessing")
        brain = BrainProcessor(args.target_brain_path, args.output_folder,
                               _args.x_pixel_mm, _args.y_pixel_mm, _args.z_pixel_mm)
        if args.save_unfiltered:
            downsampled_brain_path = os.path.join(args.output_folder, '{}_{}.nii'
                                                  .format(sample_name, 'downsampled'))
            brain.save(downsampled_brain_path)
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


if __name__ == '__main__':
    args = get_parser()

    print("Segmentation finished. Result can be found here: {}".format(process(args)))
    if args.erase_intermediate_files:
        delete_error_logs(args)
        delete_intermediate_files(args)
    if args.delete_logs:
        delete_regular_logs(args)
