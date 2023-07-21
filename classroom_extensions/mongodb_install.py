#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
An extension to install MongoDB and MongoDB Shell (mongosh).

Note: This extension assumes that you are working in Google Colab
running Ubuntu 20.04.
"""
from os import path
import os
import glob
from argparse import ArgumentParser
from IPython.core.magic import magics_class, line_magic, Magics
from .util import exec_cmd, get_os_release, is_colab

_SOFTWARE_DESC = {"mongodb": "MongoDB", "mongodb_shell": "MongoDB Shell"}

_INSTALL_CMDS = {
    "mongodb": ["apt update", "apt install mongodb", "service mongodb start"],
    "mongodb_shell": [
        "wget -qO- https://www.mongodb.org/static/pgp/server-6.0.asc |"
        "sudo tee /etc/apt/trusted.gpg.d/server-6.0.asc",
        "sudo apt-get install gnupg",
        "echo 'deb [ arch=amd64,arm64 ] "
        "https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse' | "
        "sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list",
        "sudo apt update",
        "sudo apt install -y mongodb-mongosh",
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

    @line_magic
    def install_mongodb(self, line: str):
        """Install MongoDB and MongoDB Shell"""

        if not self._meet_requirements():
            print(
                "Note: the magics for installing and configuring "
                "MongoDB may not work outside Google Colab"
            )

        args = self._arg_parser.parse_args(line.split() if line else "")
        self.install_software("mongodb")
        self.install_software("mongodb_shell")
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
        ipython.register_magics(MongoDBInstaller(ipython))
    except NameError:
        print("IPython shell not available.")
