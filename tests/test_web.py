#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests the JavaScript magics """

import unittest
from os import path

from IPython.utils import io

import classroom_extensions.web as node_ext
from classroom_extensions.web import JavascriptWithConsole, HTMLWithConsole
from .base import BaseTestCase


class TestNodeJs(BaseTestCase):
    """Testcase for the NodeJs extension"""

    def setUp(self) -> None:
        # Loads the extension
        self.ipython.extension_manager.load_extension("classroom_extensions.web")

    def tearDown(self) -> None:
        self.ipython.extension_manager.unload_extension("classroom_extensions.web")

    def test_node_script(self):
        """Tests executing server-side JavaScript"""
        print("Test executing Node.js script.")
        cell_output: str
        console_content = "------"
        with io.capture_output() as captured:
            self.ipython.run_cell_magic(
                "javascript",
                line="--target=node --filename=/tmp/test.js",
                cell=f"console.log('{console_content}');\n",
            )
            cell_output = captured.stdout
        self.assertEqual(cell_output.strip(), console_content)

    def test_save_on_disk(self):
        """Tests saving script to disk"""
        print("Test on saving a script on disk.")
        tmp_file = "/tmp/test_disk.js"
        self.ipython.run_cell_magic(
            "javascript",
            line=f"--target=disk --filename={tmp_file}",
            cell="console.log('------');\n",
        )
        self.assertEqual(path.exists(tmp_file), True)
        try:
            self.ipython.run_cell_magic(
                "javascript", line="--target=disk", cell="console.log(' ');\n"
            )
        except ValueError:
            pass

    # def test_node_server(self):
    #     """Tests the creation of a Node.js server"""
    #     print("Testing executing Node.js server...")
    #     cell_output: str
    #     cell_content = """
    #         const http = require('http')
    #
    #         const hostname = 'localhost'
    #         const port = process.env.NODE_PORT || 3000
    #
    #         const server = http.createServer((req, res) => {
    #             res.statusCode = 200
    #             res.setHeader('Content-Type', 'text/plain')
    #             res.end('Hello world!')
    #         })
    #
    #         server.listen(port, hostname, () => {
    #             console.log(`Server listening at http://${hostname}:${port}/`)
    #         })
    #     """
    #     with io.capture_output() as captured:
    #         self.ipython.run_cell_magic(
    #             "javascript",
    #             line="--target=node --filename=/tmp/server.js --port=3000",
    #             cell=f"{cell_content}",
    #         )
    #         cell_output = captured.stdout
    #     self.assertRegex(cell_output.strip(), r"(Killing|Server)")

    def test_javascript(self):
        """Tests normal JavaScript code"""
        print("Testing JavaScript with console...")

        expected_dir = {
            "text/plain": f"<{JavascriptWithConsole.__module__}."
            f"{JavascriptWithConsole.__qualname__} object>"
        }
        cell_content = "console.log('----');"
        self.ipython.run_cell_magic("javascript", line="", cell=f"{cell_content}")
        self.assertEqual(expected_dir, self.publisher.display_output.pop())

    def test_html_javascript(self):
        """Test HTML with JavaScript"""
        print("Testing HTML with JavaScript")
        expected_dir = {
            "text/plain": f"<{HTMLWithConsole.__module__}."
            f"{HTMLWithConsole.__qualname__} object>"
        }
        cell_content = "console.log('----');"
        self.ipython.run_cell_magic("html", line="--console", cell=f"{cell_content}")
        self.assertEqual(expected_dir, self.publisher.display_output.pop())

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

    def test_incorrect_loading(self):
        """Tests incorrectly loading the extension."""
        expected = "IPython shell not available.\n"
        output = self.capture_output(node_ext.load_ipython_extension, None)
        self.assertEqual(output, expected)
        output = self.capture_output(node_ext.unload_ipython_extension, None)
        self.assertEqual(output, expected)

    def test_http_server(self):
        """Tests start/stop of HTTP server"""
        self.ipython.run_line_magic(
            "http_server",
            line="--action=start --bind=0.0.0.0 --port=8000 --directory=/tmp",
        )
        self.ipython.run_line_magic("http_server", line="--action=stop --port=8000")


if __name__ == "__main__":
    unittest.main()
