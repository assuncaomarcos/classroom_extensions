#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Some helper functions """

import subprocess
import os
import pwd


_IN_COLAB = False
try:
    import google.colab

    _IN_COLAB = True
except ModuleNotFoundError:
    _IN_COLAB = False


def get_os_release() -> str:
    """Get Ubuntu's release number (e.g. 20.04)"""
    rls_version: str = ""
    with open("/etc/os-release", "r", encoding="utf-8") as release_file:
        for line in release_file:
            if line.startswith("VERSION_ID="):
                rls_version = line.split("=")[1].strip('" \n')
                break
    return rls_version


def exec_cmd(command: str) -> None:
    """
    Execute a command and print error, if occurs

    Args:
        command: the command to execute

    Returns:
        None
    """
    try:
        subprocess.check_output(
            f"{command} > /dev/null", shell=True, stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError as process_error:
        print(f"Error occurred: {process_error.output.decode()}")


def is_colab() -> bool:
    """
    Check if running on Google Colab

    Returns:
        True if running on Google Colab
    """
    return _IN_COLAB


def get_user() -> str:
    """Get the username of the user the code runs under"""

    uid = os.getuid()
    return pwd.getpwuid(uid).pw_name


def is_extension() -> bool:
    """
    Check if the code has been loaded with %load_ext

    Returns:
        True if loaded as extension via %load_ext
    """
    return "__IPYTHON__" in globals()
