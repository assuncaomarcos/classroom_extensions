#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
An extension to install MariaDB, create the config file required by the
MariaDB Jupyter to access it, and load a sample database.

Note: This extension assumes that you are working in Google Colab
running Ubuntu 20.04.
"""
from IPython.core.getipython import get_ipython
from IPython.core.magic import register_line_magic
from .util import exec_cmd, get_os_release, is_colab, get_user
import argparse

SAMPLE_DB = "https://www.mariadbtutorial.com/wp-content/uploads/2019/10/nation.zip"
START_DB_TIMEOUT = 5  # Timeout for starting MariaDB


def meet_requirements() -> bool:
    """ Check if running on Colab with the right Ubuntu release """
    return True if is_colab() and get_os_release().startswith('20.') else False


def _start_mariadb() -> None:
    """ Start MariaDB """
    import time
    get_ipython().system_raw('service mysql start &')
    print("Waiting for a few seconds for MariaDB server to start...")
    time.sleep(START_DB_TIMEOUT)


@register_line_magic
def install_mariadb(line: str):
    """ Install MariaDB, mariadb_kernel, sqlparse, etc """
    if not meet_requirements():
        print("Note: the magics for installing and configuring "
              "MariaDB may not work outside Google Colab")

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--password", type=str, default=None,
                        help="the password for the root user")
    parser.add_argument("-s", "--sample_db", action='store_true',
                        help="the password for the root user")

    args = parser.parse_args(line.split() if line else "")
    if args.password is None:
        print("Error: you must provide a password using --password=password")
        return

    db_user = get_user()
    db_pass = args.password
    load_sample_db = args.sample_db
    print("Running apt update...")
    exec_cmd("apt update -y")
    print("Installing MariaDB...")
    exec_cmd("apt install mariadb-server libmariadb-dev libmariadb3 -y")
    print("Installing required python packages...")
    exec_cmd("pip3 install mariadb==1.0.11 mariadb_kernel==0.2.0 sqlparse==0.4.4")

    from os import path
    import json

    _start_mariadb()  # First start MariaDB

    sql_stmt = f"ALTER USER '{db_user}'@'localhost' IDENTIFIED BY '{db_pass}'"
    exec_cmd(f"mariadb -e \"{sql_stmt}\"")
    exec_cmd("mkdir -p ~ /.jupyter")  # the config file must go in .jupyter
    config_path = path.join(path.expanduser("~"), ".jupyter/mariadb_config.json")
    client_conf = {
        "user": "root",
        "host": "localhost",
        "port": "3306",
        "password": db_pass,
        "start_server": "False",
        "client_bin": "/usr/bin/mariadb",
        "server_bin": "/usr/bin/mariadbd",
        "socket": "/run/mysqld/mysqld.sock"
    }
    with open(config_path, "w") as f:
        f.write(json.dumps(client_conf, indent=4))

    # Load the sample database, if required
    if load_sample_db:
        _load_sample_db(db_user, db_pass)


def _load_sample_db(db_user: str, db_pass: str):
    """ Configure a sample MariaDB database """
    exec_cmd(f"wget {SAMPLE_DB}")
    exec_cmd("unzip -o nation.zip")
    print("Importing nation database...")
    exec_cmd(f"mariadb -e \"source nation.sql\" --user={db_user} --password={db_pass}")
    print("Done.")
    exec_cmd("rm nation.zip")
