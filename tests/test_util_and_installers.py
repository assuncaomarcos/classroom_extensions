#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests for utility functions and installer extensions """

import unittest
import builtins
from unittest.mock import patch

from classroom_extensions.util import is_extension, is_colab, get_user, get_os_release
import classroom_extensions.node_install as node_install_ext
import classroom_extensions.mariadb_install as mariadb_install_ext
import classroom_extensions.mongodb_install as mongodb_install_ext
from .base import BaseTestCase


class TestUtilAndInstallers(BaseTestCase):
    """Testcase for util and installer modules"""

    def test_is_extension(self):
        """Tests is_extension check"""
        self.assertTrue(is_extension())
        with patch.object(builtins, "__IPYTHON__", create=True):
            delattr(builtins, "__IPYTHON__")
            self.assertFalse(is_extension())
            setattr(builtins, "__IPYTHON__", True)

    def test_get_user(self):
        """Tests get_user helper"""
        user = get_user()
        self.assertIsInstance(user, str)
        self.assertTrue(len(user) > 0)

    def test_is_colab(self):
        """Tests is_colab helper"""
        self.assertIsInstance(is_colab(), bool)

    def test_node_installer_parser(self):
        """Tests NodeInstaller argument parser versions"""
        installer = node_install_ext.NodeInstaller(self.ipython)
        parser = installer._create_parser()
        args = parser.parse_args(["-v", "20"])
        self.assertEqual(args.version, 20)
        args = parser.parse_args(["-v", "22"])
        self.assertEqual(args.version, 22)
        args = parser.parse_args([])
        self.assertEqual(args.version, node_install_ext._NODE_MAJOR)

    def test_node_installer_load_unload(self):
        """Tests loading and unloading node_install extension"""
        node_install_ext.load_ipython_extension(self.ipython)
        self.assertTrue(hasattr(self.ipython, "node_installer"))
        node_install_ext.unload_ipython_extension(self.ipython)
        self.assertFalse(hasattr(self.ipython, "node_installer"))

        expected = "IPython shell not available.\n"
        output = self.capture_output(node_install_ext.load_ipython_extension, None)
        self.assertEqual(output, expected)
        output = self.capture_output(node_install_ext.unload_ipython_extension, None)
        self.assertEqual(output, expected)

    def test_mariadb_installer_load_unload(self):
        """Tests loading and unloading mariadb_install extension"""
        mariadb_install_ext.load_ipython_extension(self.ipython)
        self.assertTrue(hasattr(self.ipython, "mariadb_installer"))
        mariadb_install_ext.unload_ipython_extension(self.ipython)
        self.assertFalse(hasattr(self.ipython, "mariadb_installer"))

        expected = "IPython shell not available.\n"
        output = self.capture_output(mariadb_install_ext.load_ipython_extension, None)
        self.assertEqual(output, expected)
        output = self.capture_output(mariadb_install_ext.unload_ipython_extension, None)
        self.assertEqual(output, expected)

    def test_mongodb_installer_load_unload(self):
        """Tests loading and unloading mongodb_install extension"""
        mongodb_install_ext.load_ipython_extension(self.ipython)
        self.assertTrue(hasattr(self.ipython, "mongodb_installer"))
        mongodb_install_ext.unload_ipython_extension(self.ipython)
        self.assertFalse(hasattr(self.ipython, "mongodb_installer"))

        expected = "IPython shell not available.\n"
        output = self.capture_output(mongodb_install_ext.load_ipython_extension, None)
        self.assertEqual(output, expected)
        output = self.capture_output(mongodb_install_ext.unload_ipython_extension, None)
        self.assertEqual(output, expected)


if __name__ == "__main__":
    unittest.main()
