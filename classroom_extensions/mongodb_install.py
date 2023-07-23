#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
An extension to install MongoDB and MongoDB Shell (mongosh).

Note: This extension assumes that you are working in Google Colab
running Ubuntu 22.04.
"""
from os import path
import os
import glob
import time
from argparse import ArgumentParser
from IPython.core.getipython import get_ipython
from IPython.core.magic import magics_class, line_magic, Magics
from .util import exec_cmd, get_os_release, is_colab

__all__ = ["load_ipython_extension", "unload_ipython_extension", "MongoDBInstaller"]

_START_DB_TIMEOUT = 5  # Timeout for starting MongoDB
_SOFTWARE_DESC = {"mongo": "MongoDB"}

_INSTALL_CMDS = {
    "mongo": [
        "apt update -y",
        "apt-get install gnupg curl",
        """curl -fsSL https://pgp.mongodb.com/server-6.0.asc | \
             gpg -o /usr/share/keyrings/mongodb-server-6.0.gpg \
             --dearmor""",
        "sudo apt-get install gnupg",
        "echo 'deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-6.0.gpg ] "
        "https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/6.0 multiverse' "
        "| tee /etc/apt/sources.list.d/mongodb-org-6.0.list",
        "apt update -y",
        "apt-get install -y mongodb-org",
    ],
}

_SAMPLE_DBS_URL = "https://github.com/neelabalan/mongodb-sample-dataset.git"


@magics_class
class MongoDBInstaller(Magics):
    """
    Implements the behaviour of the magic for installing MongoDB
    and MongoDB Shell on Google Colab.
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
            "-s",
            "--sample_dbs",
            action="store_true",
            help="To import the sample databases",
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

    @staticmethod
    def install_software(software: str) -> None:
        """Installs a given software"""
        description = _SOFTWARE_DESC.get(software)
        commands = _INSTALL_CMDS.get(software)

        print(f"Installing {description}...")
        try:
            for cmd in commands:
                exec_cmd(cmd)
            print(f"{description} is installed.")
        except RuntimeError as runtime_error:
            print(f"Error installing {description}: {runtime_error}")

    @staticmethod
    def import_sample_datasets() -> None:
        """Clones the git repository with multiple sample datasets and imports them"""
        local_clone = "sample_dbs"
        print("Cloning git repository with the sample datasets...")
        clone_path = path.join(os.getcwd(), local_clone)
        try:
            if not path.exists(clone_path):
                exec_cmd(f"git clone {_SAMPLE_DBS_URL} {local_clone}")
            else:
                print("Skipping git clone as local repository seems to exist.")

            datasets = [
                f
                for f in os.listdir(local_clone)
                if not path.isfile(path.join(local_clone, f))
            ]
            for dataset in datasets:
                dataset_path = path.join(clone_path, dataset)
                print(f"Importing dataset {dataset}...")
                for json_file in glob.glob(f"{dataset_path}/*.json"):
                    collection = path.splitext(path.basename(json_file))[0]
                    cmd = (
                        f"mongoimport --drop --host localhost --port 27017 "
                        f"--db {dataset} --collection {collection} --file {json_file}"
                    )
                    exec_cmd(cmd)
            print("Finished importing the sample datasets.")
        except RuntimeError as runtime_error:
            print(f"Error importing sample databases: {runtime_error}")

    @staticmethod
    def _start_mongodb() -> None:
        """Starts MongoDB"""

        get_ipython().system_raw("mongod --config /etc/mongod.conf &")
        print("Waiting for a few seconds for MongoDB server to start...")
        time.sleep(_START_DB_TIMEOUT)

    @line_magic
    def install_mongodb(self, line: str):
        """Install MongoDB and MongoDB Shell"""

        if not self._meet_requirements():
            print(
                "Note: the magics for installing and configuring "
                "MongoDB may not work outside Google Colab"
            )

        args = self._arg_parser.parse_args(line.split() if line else "")
        self.install_software("mongo")
        self._start_mongodb()

        if args.sample_dbs:
            self.import_sample_datasets()


def load_ipython_extension(ipython):
    """
    Loads the ipython extension

    Args:
        ipython: (InteractiveShell) The currently active `InteractiveShell` instance.

    Returns:
        None
    """
    try:
        mongodb_installer = MongoDBInstaller(ipython)
        ipython.register_magics(mongodb_installer)
        ipython.mongodb_installer = mongodb_installer
    except (NameError, AttributeError):
        print("IPython shell not available.")


def unload_ipython_extension(ipython):
    """Does some clean up"""

    try:
        del ipython.mongodb_installer
    except (NameError, AttributeError):
        print("IPython shell not available.")
