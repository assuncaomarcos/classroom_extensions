#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from .base import BaseTestCase


MARIADB_USER = 'testuser'
MARIADB_PASSWORD = 'testpassword'


class TestMariaDB(BaseTestCase):
    """ Testcase for the MariaDB extension """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()

        # Create the MariaDB kernel config file
        cls._create_mariadb_config()

    def setUp(self):
        # Custom path to MariaDB kernel config
        self.ipython.run_line_magic('env', 'JUPYTER_CONFIG_DIR /tmp/')

        # Load the mariadb extension
        self.ipython.extension_manager.load_extension('classroom_extensions.mariadb')

    def tearDown(self):
        self.ipython.extension_manager.unload_extension('classroom_extensions.mariadb')

    def test_show_databases(self):
        print("Testing SHOW DATABASES command.")
        self.ipython.run_cell_magic('sql', line='', cell="SHOW DATABASES;")
        pattern = r"<TABLE BORDER=1><TR><TH>Database</TH></TR><TR><TD>(.*?)</TD></TR>.+</TABLE>"
        self.assertRegex(text=str(self.publisher.display_output.pop()),
                         expected_regex=pattern)

    @classmethod
    def _create_mariadb_config(cls):
        """
        Create the MariaDB kernel config file required by the MariaDB extension.
        The file contains information on how to access the MariaDB server
        """
        from os import path
        import json
        config_path = path.join("/tmp", "mariadb_config.json")
        client_conf = {
            "user": f"{MARIADB_USER}",
            "host": "localhost",
            "port": 3306,
            "password": f"{MARIADB_PASSWORD}",
            "start_server": "False",
            "client_bin": "/usr/bin/mariadb",
            "socket": "/var/run/mysqld/mysqld.sock"
        }
        with open(config_path, "w") as f:
            f.write(json.dumps(client_conf, indent=4))
            f.flush()


if __name__ == '__main__':
    unittest.main()
