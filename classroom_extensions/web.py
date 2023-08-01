#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
The code customizes IPython's %%javascript magic by introducing line arguments
that allow for executing the JavaScript code on the server side (via Node.js).
When executed on the browser, the magic creates a section in the code cell that
mimics the browser's console. It also customizes `%%html` to enable the result
section of the cell to mimic the browser's console.
"""

from functools import partial
from typing import Any, Callable, AnyStr
from os import path, environ
from asyncio import streams
import asyncio
import contextlib
import io
import uuid
import shutil
import sys
import os
import psutil
from IPython.core.magic import magics_class, cell_magic, line_magic
from IPython.core.magics.display import DisplayMagics
from IPython.display import display, Javascript, HTML
from IPython.core import magic_arguments
from IPython.utils.process import arg_split

__all__ = [
    "load_ipython_extension",
    "unload_ipython_extension",
    "WebMagics",
    "JavascriptWithConsole",
    "HTMLWithConsole",
    "NodeProcessManager",
]

# timeout to wait for a node server process to start (in seconds)
START_SERVER_TIMEOUT = 5

# This code JavaScript will be included with the cell's code to
# redirect the output of calls to console.[log, error, warn] to the
# result section of the cell
_CELL_CONSOLE = """
function c_msg(type, o_func, ...args) {
    let p = document.createElement("p");
    p.classList.add(`console-${type}`);
    p.textContent = args.join(" ");
    document.getElementById('console-box').appendChild(p);
    o_func(...args);
}

const o_log = console.log.bind(console)
const o_error = console.error.bind(console);
const o_warn = console.warn.bind(console);

console.log = c_msg.bind(console, 'log', o_log);
console.error = c_msg.bind(console, 'error', o_error);
console.warn = c_msg.bind(console, 'warn', o_warn);

window.addEventListener("error", (event) => {
    console.error(`${event.type}: ${event.message}`);
});

var console_elems = {}
console_elems.stl = document.createElement('style');
console_elems.stl.textContent = `
:root {
    --font-log: Consolas, Monaco, 'Courier New', monospace;
}

.console-box {
    max-width: 70vw;
}

.console-error, .console-log, .console-warn {
    font-family: var(--font-log);
    white-space: nowrap;
    font-weight: 520;
    font-size: 0.9rem;
    line-height: 1.1rem;
    padding: 2px 10px;
    overflow-y: auto;
    border-bottom: 1px solid #A9A9A9;
    color: black;
    margin: 0;
}

.console-error {
    color: #8B0000;
    border-bottom-color: #FFC0CB;
    background-color: #FFE4E1;
}

.console-warn {
    color: #A0522D;
    border-bottom-color: #FFDEAD;
    background-color: #FFFACD;
}

@media (max-width: 600px) {
    .console-box {
        max-width: 95vw;
    }
}

@media (max-width: 992px) {
    .console-box {
        max-width: 90vw;
    }
}

@media (min-width: 993px) {
    .console-box {
        max-width: 85vw;
    }
}

@media (min-width: 1200px) {
    .console-box {
        max-width: 70vw;
    }
}
`;
document.head.appendChild(console_elems.stl);
console_elems.c_box = document.createElement('div');
console_elems.c_box.className = 'console-box';
console_elems.c_box.id = 'console-box';
document.getElementById('output-footer').appendChild(console_elems.c_box);
"""

_CONSOLE_TITLE = """
var console_elems = {}
console_elems.stl = document.createElement('style');
console_elems.stl.textContent = `
:root {
    --font-title: 'Lato', 'Lucida Grande', 'Lucida Sans Unicode', Tahoma, Sans-Serif;
}
.console-title {
    font-family: var(--font-title);
    font-weight: 700;
    color: black;
    font-size: 1.1rem;
    line-height: 1;
    padding: 9px 10px;
    white-space: nowrap;
    margin: 0;
}
`;
document.head.appendChild(console_elems.stl);
console_elems.h_title = document.createElement('h2');
console_elems.h_title.className = 'console-title';
console_elems.h_title.textContent = 'Console:';
document.getElementById('output-footer').appendChild(console_elems.h_title);
"""


class NodeProcessManager:
    """Used to manage the execution of Node processes"""

    _node_cmd: str = "/usr/bin/node"

    def __init__(self):
        self._daemons: dict[int, Any] = {}
        self._node_cmd = shutil.which(
            "node"
        )  # Try to discover full path of node command

    @classmethod
    async def read_stream(
        cls,
        proc,
        stream: streams.StreamReader,
        callback: Callable[[AnyStr], None],
    ) -> None:
        """
        Reads the stout/stderr stream of a given process

        Args:
            proc: the process to read the output from
            stream: the stream to read from
            callback: the callback function to call when data is read

        Returns:
            None
        """
        while proc.returncode is None:
            data = await stream.readline()
            if not data:
                break
            callback(data.decode().rstrip())

    @contextlib.asynccontextmanager
    async def open_process(
        self,
        cmd: str,
        *cmd_args: dict,
        work_dir: str = None,
        env_vars: dict = None,
        daemon: bool = False,
        stdout_callback: Callable[[AnyStr], None] = print,
    ) -> None:
        """
        Creates a new Node process

        Args:
            cmd: the command to execute
            *cmd_args: the command arguments
            work_dir: the path to the working directory
            env_vars: the environment variables to set
            daemon: True if the process will run in background
            stdout_callback: the callback function to call when reading the output stream

        Returns:
            None
        """
        proc = await asyncio.create_subprocess_exec(
            cmd,
            *cmd_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=work_dir,
            env=env_vars,
        )
        stream_task = asyncio.create_task(
            self.read_stream(proc, proc.stdout, stdout_callback)
        )

        async def server_wait() -> None:
            """Shields the execution and stream reader tasks for a background process"""
            server_task = asyncio.create_task(proc.wait())
            try:
                await asyncio.shield(server_task)
                await asyncio.shield(stream_task)
            except asyncio.CancelledError:
                pass

        try:
            yield proc
        finally:
            if not daemon:
                await proc.wait()
                await stream_task
            else:
                try:
                    await asyncio.wait_for(server_wait(), START_SERVER_TIMEOUT)
                except asyncio.TimeoutError:
                    pass

    async def execute(
        self,
        js_file: str = None,
        port: int = None,
        stdout_callback: Callable[[AnyStr], None] = partial(print, flush=True),
    ) -> None:
        """
        Use Node.js to run the provided script. If a port is given,
        the script will be run in background without blocking the cell

        Args:
            js_file: the full path to the JavaScript file
            port: the port number for the server
            stdout_callback: the callback function to call when reading the output stream

        Returns:
            None
        """
        server_env = environ.copy()
        if port:
            self.kill_daemon(port)  # Kill any Node process using the port
            server_env["NODE_PORT"] = str(port)

        work_dir = path.dirname(path.realpath(js_file))
        daemon = port is not None
        async with self.open_process(
            self._node_cmd,
            js_file,
            work_dir=work_dir,
            env_vars=server_env,
            daemon=daemon,
            stdout_callback=stdout_callback,
        ) as proc:
            if daemon:
                self._daemons[port] = proc

    @classmethod
    def _force_kill(cls, port: int) -> None:
        """To kill a Node.js process listening on a given port"""
        for proc in psutil.process_iter(["pid", "name", "connections"]):
            try:
                for conn in proc.connections():
                    if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
                        print(
                            f"Killing existing {proc.name()} process, id {proc.pid} "
                            f"and listening on port {port}",
                            flush=True,
                        )
                        proc.kill()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

    def kill_daemon(self, port: int) -> None:
        """
        Kills a previously started background process

        Args:
            port: the port the daemon is likely listening to

        Returns:
            None
        """
        if port in self._daemons:
            process = self._daemons[port]
            try:
                process.kill()
            except ProcessLookupError:
                print(f"No node process on port {port}, ok to continue...")
        else:
            self._force_kill(port)

    def clean_up(self) -> None:
        """Some cleanup during testing and extension unloading"""
        for proc in self._daemons.values():
            try:
                proc.terminate()
            except ProcessLookupError as process_error:
                print(f"Error: process not found {process_error}")
        self._daemons.clear()

    def __del__(self):
        self.clean_up()


class JavascriptWithConsole(Javascript):
    """
    This class extends JavaScript to intercept calls to console.log
    and make a result section of the cell.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _repr_javascript_(self):
        """Creates the full JavaScript code to be delivered to the browser"""
        return _CELL_CONSOLE + super()._repr_javascript_()


class HTMLWithConsole(HTML):
    """
    This adds a copy of the browser's console with the messages
    triggered when loading/executing the HTML/JavaScript code.
    """

    def __init__(self, data: AnyStr = None, console: bool = False):
        """
        Creates a new object representing the HTML code to be rendered.

        Args:
            data: the HTML content
            console: True if the browser console must be displayed
        """
        super().__init__(data=data)
        self.console = console

    def _repr_html_(self) -> str:
        """
        Creates the HTML content.

        Returns:
            The HTML code to be rendered.
        """
        html: str = ""
        if self.console:
            html += f"<script>{_CONSOLE_TITLE}{_CELL_CONSOLE}</script>"
        return html + super()._repr_html_()


def javascript_args(func):
    """Single decorator for adding JavaScript args"""
    args = [
        magic_arguments.argument(
            "-t",
            "--target",
            type=str,
            choices=["browser", "node", "disk"],
            default="browser",
            help="the target for script execution",
        ),
        magic_arguments.argument(
            "-f",
            "--filename",
            type=str,
            help="filename when cell contents are saved to disk",
        ),
        magic_arguments.argument(
            "-p",
            "--port",
            type=int,
            help="a port number if the cell starts a Node server process",
        ),
    ]
    for arg in args:
        func = arg(func)
    return func


def html_args(func):
    """Single decorator for adding HTML args"""
    args = [
        magic_arguments.argument(
            "-c",
            "--console",
            action="store_true",
            help="Whether to display a copy of the browser's console or not",
        )
    ]
    for arg in args:
        func = arg(func)
    return func


def http_server_args(func):
    """Single decorator for adding HTTP server args"""
    args = [
        magic_arguments.argument(
            "--action",
            "-a",
            default="start",
            choices=["start", "stop"],
            help="action to execute (default: start)",
        ),
        magic_arguments.argument(
            "--bind",
            "-b",
            default="0.0.0.0",
            help="specify alternate bind address (default: all interfaces)",
        ),
        magic_arguments.argument(
            "--directory",
            "-d",
            default=os.getcwd(),
            help="specify alternate directory (default: current directory)",
        ),
        magic_arguments.argument(
            "--port",
            "-p",
            default=8000,
            type=int,
            help="specify alternate port (default: 8000)",
        ),
    ]
    for arg in args:
        func = arg(func)
    return func


@magics_class
class WebMagics(DisplayMagics):
    """
    Implements the customizations to the %%javascript magic
    that enables JavaScript execution by Node.js
    """

    _proc_mgmt: NodeProcessManager
    _in_notebook: bool

    def __init__(self, shell):
        super().__init__(shell=shell)
        self._proc_mgmt = NodeProcessManager()
        self._in_notebook = shell.has_trait("kernel")

    @staticmethod
    def _save_script(filename: str, cell_content: str) -> str:
        """
        Creates the JavaScript file for Node to run

        Args:
            filename: the file name
            cell_content: the cell contents to save into the file

        Returns:
            Name of the file created
        """
        if not filename:
            filename = f"{uuid.uuid4().hex}.js"
        with io.open(filename, "w", encoding="utf-8") as script_file:
            script_file.write(cell_content)
        return filename

    def _run_on_node(self, js_file: str, port: int = None) -> None:
        """
        Triggers the execution on Node.js

        Args:
            js_file: path to the file to execute
            port: the port number to use, if the scripts launches a server

        Returns:
            None
        """
        if self._in_notebook:
            loop = asyncio.get_event_loop()
            loop.create_task(self._proc_mgmt.execute(js_file, port))
        else:
            asyncio.run(self._proc_mgmt.execute(js_file, port))

    @magic_arguments.magic_arguments()
    @javascript_args
    @cell_magic
    def javascript(self, line: str = None, cell: str = None) -> None:
        """
        Method called when executing %%javascript
        Args:
            line: line arguments (e.g. --target, --filename)
            cell: the JavaScript code to execute

        Returns:
            None
        """
        argv = arg_split(line, posix=not sys.platform.startswith("win"))
        args = self.javascript.parser.parse_args(argv)

        if args.target == "node":
            if not args.filename:
                raise ValueError("--filename is required when using --target=node")
            js_file = self._save_script(args.filename, cell)
            self._run_on_node(js_file, args.port)
        elif args.target == "browser":
            display(JavascriptWithConsole(cell))
        elif args.target == "disk":
            if not args.filename:
                raise ValueError("--filename is required when using --target=disk")
            self._save_script(args.filename, cell)

    @magic_arguments.magic_arguments()
    @html_args
    @cell_magic
    def html(self, line=None, cell=None) -> None:
        argv = arg_split(line, posix=not sys.platform.startswith("win"))
        args = self.html.parser.parse_args(argv)
        html = HTMLWithConsole(cell, args.console)
        display(html)

    @magic_arguments.magic_arguments()
    @http_server_args
    @line_magic
    def http_server(self, line=None) -> None:
        """Line magic to start/stop a python Web server"""
        argv = arg_split(line, posix=not sys.platform.startswith("win"))
        args = self.http_server.parser.parse_args(argv)

        def start_web_server(address, directory, port):
            stop_web_server(port)  # Stop any server that is currently running
            print(f"Starting server listening on port {port}...")
            self.shell.system_raw(
                f"python -m http.server {port} --bind {address} --directory {directory} &"
            )

        def stop_web_server(port):
            print(f"Stopping any server listening on port {port}...")
            stop_cmd = (
                r"ps -x | grep -e '[h]ttp.server\s*"
                + str(port)
                + "' | awk '{print $1}' | xargs -I {} kill {}"
            )
            self.shell.system_raw(stop_cmd)

        if args.action == "start":
            start_web_server(args.bind, args.directory, args.port)
        else:
            stop_web_server(args.port)


def load_ipython_extension(ipython):
    """
    Loads the ipython extension

    Args:
        ipython: (InteractiveShell) The currently active `InteractiveShell` instance.

    Returns:
        None
    """
    try:
        web_magics = WebMagics(ipython)
        ipython.register_magics(web_magics)
        ipython.node_magics = web_magics
    except (NameError, AttributeError):
        print("IPython shell not available.")


def unload_ipython_extension(ipython):
    """Unloads the extension"""
    try:
        del ipython.web_magics
    except (NameError, AttributeError):
        print("IPython shell not available.")
