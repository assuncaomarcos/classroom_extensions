#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Install MongoDB and import sample databases """

import subprocess
from os import path
import os
import glob


SOFTWARE_DESC = {"mongodb": "MongoDB", "mongodb_shell": "MongoDB Shell"}

INSTALL_CMDS = {
    "mongodb": ["apt update", "apt install mongodb", "service mongodb start"],
    "mongodb_shell": [
        "wget -qO- https://www.mongodb.org/static/pgp/server-6.0.asc | sudo tee /etc/apt/trusted.gpg.d/server-6.0.asc",
        "sudo apt-get install gnupg",
        "echo 'deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse' | "
        "sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list",
        "sudo apt update",
        "sudo apt install -y mongodb-mongosh",
    ],
}

SAMPLE_DBS_URL = "https://github.com/neelabalan/mongodb-sample-dataset.git"


def exec_cmd(command: str) -> None:
    """
    Execute a command and print error, if occurs

    Args:
        command: (str) the command to execute

    Returns:
        None
    """
    try:
        subprocess.check_output(
            f"{command} > /dev/null", shell=True, stderr=subprocess.STDOUT
        )
    except (subprocess.CalledProcessError, Exception) as process_error:
        raise RuntimeError(f"Error with: {command}\n") from process_error


def install_software(software: str) -> None:
    """Installs a given software"""
    description = SOFTWARE_DESC.get(software)
    commands = INSTALL_CMDS.get(software)

    print(f"Installing {description}...")
    try:
        for cmd in commands:
            exec_cmd(cmd)
        print(f"{description} is installed.")
    except RuntimeError as runtime_error:
        print(f"Error installing {description}: {runtime_error}")


def import_sample_datasets() -> None:
    """Clones the git repository with multiple sample datasets and imports them"""
    local_clone = "sample_dbs"
    print("Cloning git repository with the sample datasets...")
    clone_path = path.join(os.getcwd(), local_clone)
    try:
        if not path.exists(clone_path):
            exec_cmd(f"git clone {SAMPLE_DBS_URL} {local_clone}")
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


install_software("mongodb")
install_software("mongodb_shell")
import_sample_datasets()
