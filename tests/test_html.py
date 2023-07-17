#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests the HTML magics """

import unittest
from classroom_extensions.html import HTMLWithConsole
import classroom_extensions.html as html_ext
from .base import BaseTestCase


class TestHTML(BaseTestCase):
    """Testcase for the HTML extension"""

    def setUp(self) -> None:
        self.ipython.extension_manager.load_extension("classroom_extensions.html")

    def tearDown(self):
        self.ipython.extension_manager.unload_extension("classroom_extensions.html")

    def test_javascript(self):
        """Test HTML with JavaScript"""
        print("Testing HTML with JavaScript")
        self.ipython.extension_manager.load_extension("classroom_extensions.html")
        expected_dir = {
            "text/plain": f"<{HTMLWithConsole.__module__}."
            f"{HTMLWithConsole.__qualname__} object>"
        }
        cell_content = "console.log('----');"
        self.ipython.run_cell_magic("html", line="--console", cell=f"{cell_content}")
        self.assertEqual(expected_dir, self.publisher.display_output.pop())
        self.ipython.extension_manager.unload_extension("classroom_extensions.html")

    def test_html_console(self):
        """Tests the HTML with console."""

        html_code = """
            <div class="container">
            <h1>An H1 Title</h1>
            <h2>An H2 Title</h2>
            <p>A paragraph with some text.</p>
            </div>
        """

        html = HTMLWithConsole(data=html_code, console=True)
        self.assertRegex(html._repr_html_(), "console_elems")

    def test_loading(self):
        """Tests incorrectly loading the extension."""
        expected = "IPython shell not available.\n"
        output = self.capture_output(html_ext.load_ipython_extension, None)
        self.assertEqual(output, expected)
        output = self.capture_output(html_ext.unload_ipython_extension, None)
        self.assertEqual(output, expected)


if __name__ == "__main__":
    unittest.main()
