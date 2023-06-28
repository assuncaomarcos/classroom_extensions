#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from IPython.testing.globalipapp import get_ipython
from IPython.utils import io
from .publisher import CaptureDisplayPub
import logging
import asyncio


class TestNodeJs(unittest.TestCase):
    """ Testcase for the NodeJs extension """

    @classmethod
    def setUpClass(cls) -> None:
        cls.ipython = get_ipython()

    def setUp(self) -> None:
        self.ipython.log.setLevel(logging.DEBUG)
        self.ipython.log.addHandler(logging.StreamHandler())

        # To be able to intercept the calls to display()
        self.publisher = CaptureDisplayPub(self.ipython.display_pub)
        self.ipython.display_pub = self.publisher

    def test_process_manager(self):
        from classroom_extensions.node import NodeProcessManager
        proc_manager = NodeProcessManager()
        where_ls = ""

        def stdout_callback(data):
            nonlocal where_ls
            where_ls += data

        async def run_cmd():
            async with proc_manager.open_process('which', 'ls', stdout_callback=stdout_callback):
                pass

        asyncio.run(run_cmd())
        self.assertRegex(text=where_ls, expected_regex=r".*/ls")

    def test_loading_extension(self):
        self.ipython.extension_manager.load_extension('classroom_extensions.node')
        self.ipython.extension_manager.unload_extension('classroom_extensions.node')

    def test_node_script(self):
        self.ipython.extension_manager.load_extension('classroom_extensions.node')
        cell_output: str
        console_content = "------"
        with io.capture_output() as captured:
            self.ipython.run_cell_magic("javascript",
                                        line="--target=node --filename=/tmp/test.js",
                                        cell=f"console.log('{console_content}');\n")
            cell_output = captured.stdout
        self.assertEqual(cell_output.strip(), console_content)
        self.ipython.extension_manager.unload_extension('classroom_extensions.node')

    def test_node_server(self):
        self.ipython.extension_manager.load_extension('classroom_extensions.node')
        cell_output: str
        expected_output = "Server listening at http://localhost:3000/"
        cell_content = """
            const http = require('http')

            const hostname = 'localhost'
            const port = process.env.NODE_PORT || 3000

            const server = http.createServer((req, res) => {
                res.statusCode = 200
                res.setHeader('Content-Type', 'text/plain')
                res.end('Hello world!')
            })

            server.listen(port, hostname, () => {
                console.log(`Server listening at http://${hostname}:${port}/`)
            })
        """
        with io.capture_output() as captured:
            self.ipython.run_cell_magic("javascript",
                                        line="--target=node --filename=/tmp/server.js --port=3000",
                                        cell=f"{cell_content}")
            cell_output = captured.stdout
        self.assertEqual(cell_output.strip(), expected_output)
        self.ipython.extension_manager.unload_extension('classroom_extensions.node')

    def test_javascript(self):
        from classroom_extensions.node import JavascriptWithConsole
        self.ipython.extension_manager.load_extension('classroom_extensions.node')
        expected_dir = {"text/plain": f"<{JavascriptWithConsole.__module__}."
                                      f"{JavascriptWithConsole.__qualname__} object>"}
        cell_content = f"console.log('----');"
        self.ipython.run_cell_magic("javascript", line="", cell=f"{cell_content}")
        self.assertEqual(expected_dir, self.publisher.display_output.pop())
        self.ipython.extension_manager.unload_extension('classroom_extensions.node')


if __name__ == '__main__':
    unittest.main()
