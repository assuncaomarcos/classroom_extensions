#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from IPython.utils import io
from .base import BaseTestCase
import asyncio


class TestNodeJs(BaseTestCase):
    """ Testcase for the NodeJs extension """

    def setUp(self) -> None:
        # Loads the extension
        self.ipython.extension_manager.load_extension('classroom_extensions.node')

    def tearDown(self) -> None:
        self.ipython.extension_manager.unload_extension('classroom_extensions.node')

    def test_process_manager(self):
        print("Test process manager.")
        from classroom_extensions.node import NodeProcessManager
        proc_manager = NodeProcessManager()
        where_ls = ""

        def stdout_callback(data):
            nonlocal where_ls
            where_ls += data

        async def run_cmd():
            async with proc_manager.open_process('which', 'uname', stdout_callback=stdout_callback):
                pass

        asyncio.run(run_cmd())
        self.assertRegex(text=where_ls, expected_regex=r"uname")

    def test_node_script(self):
        print("Test executing Node.js script.")
        cell_output: str
        console_content = "------"
        with io.capture_output() as captured:
            self.ipython.run_cell_magic("javascript",
                                        line="--target=node --filename=/tmp/test.js",
                                        cell=f"console.log('{console_content}');\n")
            cell_output = captured.stdout
        self.assertEqual(cell_output.strip(), console_content)

    def test_node_server(self):
        print("Testing executing Node.js server...")
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
        # TODO: Change this test. If the test case is run twice, it fails as another process is still running
        self.assertEqual(cell_output.strip(), expected_output)

    def test_javascript(self):
        print("Testing JavaScript with console...")
        from classroom_extensions.node import JavascriptWithConsole
        expected_dir = {"text/plain": f"<{JavascriptWithConsole.__module__}."
                                      f"{JavascriptWithConsole.__qualname__} object>"}
        cell_content = f"console.log('----');"
        self.ipython.run_cell_magic("javascript", line="", cell=f"{cell_content}")
        self.assertEqual(expected_dir, self.publisher.display_output.pop())


if __name__ == '__main__':
    unittest.main()
