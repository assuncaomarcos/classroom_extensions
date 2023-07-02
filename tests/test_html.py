#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from .base import BaseTestCase


class TestHTML(BaseTestCase):
    """ Testcase for the HTML extension """

    def setUp(self) -> None:
        self.ipython.extension_manager.load_extension('classroom_extensions.html')

    def tearDown(self):
        self.ipython.extension_manager.unload_extension('classroom_extensions.html')

    def test_javascript(self):
        print("Testing HTML with JavaScript")
        from classroom_extensions.html import HTMLWithConsole
        self.ipython.extension_manager.load_extension('classroom_extensions.html')
        expected_dir = {"text/plain": f"<{HTMLWithConsole.__module__}."
                                      f"{HTMLWithConsole.__qualname__} object>"}
        cell_content = f"console.log('----');"
        self.ipython.run_cell_magic("html", line="--console", cell=f"{cell_content}")
        self.assertEqual(expected_dir, self.publisher.display_output.pop())
        self.ipython.extension_manager.unload_extension('classroom_extensions.html')


if __name__ == '__main__':
    unittest.main()
