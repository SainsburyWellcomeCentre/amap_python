import os
import subprocess
from tempfile import gettempdir


# TODO: check if needs to extend with prefix for step and sample
def safe_execute_command(cmd, log_file_path=None, error_file_path=None):
    """
    Executes a command in the terminal, making sure that the output can
    be logged even if execution fails during the call.

    :param cmd:
    :param log_file_path:
    :param error_file_path:
    :return:
    """
    if log_file_path is None:
        log_file_path = os.path.abspath(os.path.join(gettempdir(), 'safe_execute_command.log'))
    if error_file_path is None:
        error_file_path = os.path.abspath(os.path.join(gettempdir(), 'safe_execute_command.err'))

    with open(log_file_path, 'w') as log_file, open(error_file_path, 'w') as error_file:
        try:
            subprocess.check_call(cmd, stdout=log_file, stderr=error_file, shell=True)
        except subprocess.CalledProcessError:
            raise SafeExecuteCommandError("Process {} failed, please read the logs at {} and {}".
                                          format(cmd, log_file_path, error_file_path))


class SafeExecuteCommandError(Exception):
    pass
