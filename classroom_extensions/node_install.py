#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
An extension to install more recent versions of Node.js on Google Colab.

Note: This extension assumes that you are working in Google Colab running
Ubuntu 22.04 or above.
"""
from argparse import ArgumentParser
from IPython.core.magic import magics_class, line_magic, Magics
from .util import exec_cmd, get_os_release, is_colab

__all__ = ["load_ipython_extension", "unload_ipython_extension", "NodeInstaller"]

_NODE_MAJOR = 18  # By default install version 18


@magics_class
class NodeInstaller(Magics):
    """
    Implements the behaviour of the magic for installing
    Node.js from NodeSource on Google Colab.
    """

    in_notebook: bool
    _arg_parser: ArgumentParser

    def __init__(self, shell):
        super().__init__(shell=shell)
        self._arg_parser = self._create_parser()
        self.in_notebook = shell.has_trait("kernel")

    @staticmethod
    def _create_parser() -> ArgumentParser:
        parser = ArgumentParser()
        parser.add_argument(
            "-v",
            "--version",
            choices=[16, _NODE_MAJOR, 20],
            default=_NODE_MAJOR,
            help="the Node.js version to use",
        )
        return parser

    @staticmethod
    def _meet_requirements() -> bool:
        """
        Check if running on Colab with the right Ubuntu release

        Returns:
            True if running on Google Colab on Ubuntu 2x.xx container
        """
        return is_colab() and get_os_release().startswith("2")

    @line_magic
    def install_nodejs(self, line: str):
        """Install dependencies and Node.js from NodeSource"""

        if not self._meet_requirements():
            print(
                "Note: the magics for installing and configuring "
                "Node.js from NodeSource may not work outside "
                "Google Colab"
            )

        args = self._arg_parser.parse_args(line.split() if line else "")
        print("Running apt update...")
        exec_cmd("apt update -y")

        print("Installing dependencies...")
        exec_cmd("apt-get install -y ca-certificates curl gnupg dialog apt-utils")

        print("Installing keyring...")
        exec_cmd("mkdir -p /etc/apt/keyrings")
        exec_cmd(
            "curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key "
            "| sudo gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg"
        )

        print("Adding apt source...")
        exec_cmd(
            f'echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] '
            f'https://deb.nodesource.com/node_{args.version}.x nodistro main" | '
            f"sudo tee /etc/apt/sources.list.d/nodesource.list"
        )

        print("Installing Node.js...")
        exec_cmd("apt-get update -y")
        exec_cmd("apt-get install nodejs -y")
        print("Done.")


def load_ipython_extension(ipython):
    """
    Loads the ipython extension

    Args:
        ipython: (InteractiveShell) The currently active `InteractiveShell` instance.

    Returns:
        None
    """
    try:
        node_installer = NodeInstaller(ipython)
        ipython.register_magics(node_installer)
        ipython.node_installer = node_installer
    except (NameError, AttributeError):
        print("IPython shell not available.")


def unload_ipython_extension(ipython):
    """Does some clean up"""

    try:
        del ipython.node_installer
    except (NameError, AttributeError):
        print("IPython shell not available.")
