#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests the MongoDB magics """

import unittest
import os
import uuid
from classroom_extensions.mongodb import MongoDBConfig
import classroom_extensions.mongodb as mongodb_ext
from .base import BaseTestCase

MONGO_USERNAME = "admin"
MONGO_PASSWORD = "password"
MONGO_DATABASE = "testdb"

PARAM_LINE = (
    f"--host=localhost --port=27017 "
    f"--username={MONGO_USERNAME} "
    f"--password={MONGO_PASSWORD}"
)


class TestMongoDB(BaseTestCase):
    """Testcase for the MongoDB extension"""

    config_file = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.config_file = f"{uuid.uuid4().hex}.json"

    def setUp(self) -> None:
        # Load the extension
        self.ipython.extension_manager.load_extension("classroom_extensions.mongodb")

        # Custom path to config files
        self.ipython.run_line_magic("env", "JUPYTER_CONFIG_DIR /tmp")

    def tearDown(self):
        self.ipython.extension_manager.unload_extension("classroom_extensions.mongodb")

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        os.unlink(os.path.join("/tmp", cls.config_file))

    def test_new_config(self):
        """Tests creating a new config file"""
        print("Testing new config...")
        config = MongoDBConfig(config_file=self.config_file)
        config.save()
        expected = " --host localhost --port 27017"
        self.assertEqual(expected, config.get_shell_args())

    def test_config_magic(self):
        """Tests the mongo_config line magic"""
        print("Testing mongo_config magic")
        self.ipython.run_line_magic("mongo_config", line=PARAM_LINE)

    def test_cell_magic(self):
        """Tests executing the mongo cell magic"""
        print("Testing mogo magic")
        js_code = """show dbs;
        use testdb;
        show collections;
        """
        self.capture_output(
            self.ipython.run_cell_magic, "mongo", line=PARAM_LINE, cell=js_code
        )

    def test_incorrect_loading(self):
        """Tests incorrectly loading the extension."""
        expected = "IPython shell not available.\n"
        output = self.capture_output(mongodb_ext.load_ipython_extension, None)
        self.assertEqual(output, expected)
        output = self.capture_output(mongodb_ext.unload_ipython_extension, None)
        self.assertEqual(output, expected)


if __name__ == "__main__":
    unittest.main()
