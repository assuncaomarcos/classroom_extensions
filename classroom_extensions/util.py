#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess


def get_os_release() -> str:
    """ Get Ubuntu's release number (e.g. 20.04) """
    rls_version: str = ''
    with open('/etc/os-release', 'r') as f:
        for line in f:
            if line.startswith('VERSION_ID='):
                rls_version = line.split('=')[1].strip('" \n')
                break
    return rls_version


def exec_cmd(command: str) -> None:
    """
    Execute a command and print error, if occurs
    :param command: the command to execute
    :return: None
    """
    try:
        subprocess.check_output(f"{command} > /dev/null",
                                shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        error_message = e.output.decode()
        print(f"Error occurred: {error_message}")


def is_colab() -> bool:
    """
    Check if running on Google Colab
    :return: True if running on Google Colab
    """
    try:
        import google.colab
        return True
    except ModuleNotFoundError:
        return False


def get_user() -> str:
    """ Get the username of the user the code runs under """
    import os
    import pwd

    uid = os.getuid()
    return pwd.getpwuid(uid).pw_name


def is_extension():
    """ Check if the code has been loaded with %load_ext """
    return True if '__IPYTHON__' in globals() else False
