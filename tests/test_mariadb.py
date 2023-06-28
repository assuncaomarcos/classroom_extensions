#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from IPython.testing.globalipapp import get_ipython
from testcontainers.mysql import MySqlContainer
from .publisher import CaptureDisplayPub
import os
import logging
import getpass


MARIADB_IMAGE = 'mariadb:latest'
MARIADB_USER = 'root'
MARIADB_PASSWORD = 'passw0rd'
MARIADB_DATABASE = 'test'


class TestMariaDB(unittest.TestCase):
    """ Testcase for the MariaDB extension """

    def setUp(self):
        self.ipython = get_ipython()
        self.ipython.log.setLevel(logging.DEBUG)
        self.ipython.log.addHandler(logging.StreamHandler())

        # To be able to intercept the calls to display()
        self.publisher = CaptureDisplayPub(self.ipython.display_pub)
        self.ipython.display_pub = self.publisher

        # Custom path to MariaDB kernel config
        os.environ['JUPYTER_CONFIG_DIR'] = '/tmp/'
        self.ipython.run_line_magic('env', 'JUPYTER_CONFIG_DIR')

        # Fetch and start the test container
        self.mysql = MySqlContainer(MARIADB_IMAGE,
                                    MYSQL_USER=MARIADB_USER,
                                    MYSQL_PASSWORD=MARIADB_PASSWORD,
                                    MYSQL_DATABASE=MARIADB_DATABASE)
        self.mysql.start()
        self.mysql_port = self.mysql.get_exposed_port(3306)
        self.mysql_ip = self.mysql.get_container_host_ip()

        # Create the MariaDB kernel config file
        self._create_mariadb_config()

        # Limitation by the MariaDB kernel: it requires a socket file.
        # As the tests use a "remote" docker container, the following
        # will use socat to create a socket file redirection
        command = f"socat UNIX-LISTEN:/tmp/mariadb.sock,fork,reuseaddr," \
                  f"unlink-early,user={getpass.getuser()},group={getpass.getuser()}," \
                  f"mode=777 TCP:{self.mysql_ip}:{self.mysql_port} &"
        self.ipython.system_raw(command)

    def tearDown(self):
        self.mysql.stop()
        self.mysql.get_docker_client().client.close()

    def test_loading_and_show_databases(self):
        # Load the mariadb extension
        self.ipython.extension_manager.load_extension('classroom_extensions.mariadb')

        self.ipython.run_cell_magic('sql', line='', cell="SHOW DATABASES;")
        pattern = r"<TABLE BORDER=1><TR><TH>Database</TH></TR><TR><TD>(.*?)</TD></TR>.+</TABLE>"
        self.assertRegex(text=str(self.publisher.display_output.pop()),
                         expected_regex=pattern)

        self.ipython.extension_manager.unload_extension('classroom_extensions.mariadb')

    def _create_mariadb_config(self):
        """
        Create the MariaDB kernel config file required by the MariaDB extension.
        The file contains information on how to access the MariaDB server
        """
        from os import path
        import json
        config_path = path.join(os.environ['JUPYTER_CONFIG_DIR'], "mariadb_config.json")
        client_conf = {
            "user": f"{MARIADB_USER}",
            "host": "localhost",
            "port": f"{self.mysql_port}",
            "password": f"{MARIADB_PASSWORD}",
            "start_server": "False",
            "client_bin": "/usr/bin/mariadb",
            "socket": "/tmp/mariadb.sock"
        }
        with open(config_path, "w") as f:
            f.write(json.dumps(client_conf, indent=4))
            f.flush()


if __name__ == '__main__':
    unittest.main()
