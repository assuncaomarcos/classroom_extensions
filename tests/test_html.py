#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from IPython.testing.globalipapp import get_ipython
from .publisher import CaptureDisplayPub
import logging


class TestHTML(unittest.TestCase):
    """ Testcase for the HTML extension """

    @classmethod
    def setUpClass(cls) -> None:
        cls.ipython = get_ipython()

    def setUp(self) -> None:
        self.ipython.log.setLevel(logging.DEBUG)
        self.ipython.log.addHandler(logging.StreamHandler())

        # To be able to intercept the calls to display()
        self.publisher = CaptureDisplayPub(self.ipython.display_pub)
        self.ipython.display_pub = self.publisher

    def test_loading_extension(self):
        self.ipython.extension_manager.load_extension('classroom_extensions.html')
        self.ipython.extension_manager.unload_extension('classroom_extensions.html')

    def test_javascript(self):
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
