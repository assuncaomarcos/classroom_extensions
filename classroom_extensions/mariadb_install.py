#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
An extension to install MariaDB, create the config file required by the
MariaDB Jupyter to access it, and load a sample database.

Note: This extension assumes that you are working in Google Colab
running Ubuntu 22.04.
"""
import time
from os import path
import json
from argparse import ArgumentParser
from IPython.core.magic import magics_class, line_magic, Magics
from IPython.core.getipython import get_ipython
from .util import exec_cmd, get_os_release, is_colab, get_user

__all__ = ["load_ipython_extension", "unload_ipython_extension", "MariaDBInstaller"]

_SAMPLE_DB = "https://www.mariadbtutorial.com/wp-content/uploads/2019/10/nation.zip"
_START_DB_TIMEOUT = 5  # Timeout for starting MariaDB


@magics_class
class MariaDBInstaller(Magics):
    """
    Implements the behaviour of the magic for installing MariaDB on Google Colab.
    """

    in_notebook: bool
    _arg_parser: ArgumentParser
    _db_user: str
    _db_pass: str

    def __init__(self, shell):
        super().__init__(shell=shell)
        self._arg_parser = self._create_parser()
        self.in_notebook = shell.has_trait("kernel")
        self._db_user = get_user()
        self._db_pass = ""

    @staticmethod
    def _create_parser() -> ArgumentParser:
        parser = ArgumentParser()
        parser.add_argument(
            "-p",
            "--password",
            type=str,
            default=None,
            help="the password for the root user",
        )
        parser.add_argument(
            "-s",
            "--sample_db",
            action="store_true",
            help="to load the sample database",
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
    def _start_mariadb() -> None:
        """Starts MariaDB"""

        service_name = "mariadb" if get_os_release().startswith("22") else "mysql"
        get_ipython().system_raw(f"service {service_name} start &")
        print("Waiting for a few seconds for MariaDB server to start...")
        time.sleep(_START_DB_TIMEOUT)

    @line_magic
    def install_mariadb(self, line: str):
        """Install MariaDB, mariadb_kernel, sqlparse, etc"""

        if not self._meet_requirements():
            print(
                "Note: the magics for installing and configuring "
                "MariaDB may not work outside Google Colab"
            )

        args = self._arg_parser.parse_args(line.split() if line else "")
        if args.password is None:
            print("Error: you must provide a password using --password=password")
            return

        self._db_pass = args.password
        load_sample_db = args.sample_db
        print("Running apt update...")
        exec_cmd("apt update -y")
        print("Installing MariaDB...")
        exec_cmd("apt install mariadb-server libmariadb-dev libmariadb3 -y")
        print("Installing required python packages...")
        exec_cmd("pip3 install mariadb==1.0.11 mariadb_kernel==0.2.0 sqlparse==0.4.4")

        self._start_mariadb()  # First start MariaDB

        sql_stmt = (
            f"ALTER USER '{self._db_user}'@'localhost' IDENTIFIED BY '{self._db_pass}'"
        )
        exec_cmd(f'mariadb -e "{sql_stmt}"')
        exec_cmd("mkdir -p ~ /.jupyter")  # the config file must go in .jupyter
        config_path = path.join(path.expanduser("~"), ".jupyter/mariadb_config.json")
        client_conf = {
            "user": "root",
            "host": "localhost",
            "port": "3306",
            "password": self._db_pass,
            "start_server": "False",
            "client_bin": "/usr/bin/mariadb",
            "server_bin": "/usr/bin/mariadbd",
            "socket": "/run/mysqld/mysqld.sock",
        }
        with open(config_path, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps(client_conf, indent=4))

        # Load the sample database, if required
        if load_sample_db:
            self._load_sample_db()
        print("Done.")

    def _load_sample_db(self):
        """Configure a sample MariaDB database"""
        exec_cmd(f"wget {_SAMPLE_DB}")
        exec_cmd("unzip -o nation.zip")
        print("Importing nation database...")
        exec_cmd(
            f'mariadb -e "source nation.sql" --user={self._db_user} --password={self._db_pass}'
        )
        exec_cmd("rm nation.zip")


def load_ipython_extension(ipython):
    """
    Loads the ipython extension

    Args:
        ipython: (InteractiveShell) The currently active `InteractiveShell` instance.

    Returns:
        None
    """
    try:
        mariadb_installer = MariaDBInstaller(ipython)
        ipython.register_magics(mariadb_installer)
        ipython.mariadb_installer = mariadb_installer
    except (NameError, AttributeError):
        print("IPython shell not available.")


def unload_ipython_extension(ipython):
    """Does some clean up"""

    try:
        del ipython.mariadb_installer
    except (NameError, AttributeError):
        print("IPython shell not available.")
