#!/usr/bin/env python
# -*- coding: utf-8 -*-

from IPython.core.magic import (magics_class, cell_magic)
from IPython.core.magics.display import DisplayMagics
from IPython.core.getipython import get_ipython
from IPython.display import display, Javascript
from argparse import ArgumentParser
from functools import partial
from typing import Any, Callable
from os import path, environ
import asyncio
import contextlib
import io
import uuid
import shutil
import psutil


# timeout to wait for a node server process to start (in seconds)
START_SERVER_TIMEOUT = 5


class NodeProcessManager(object):
    """ Used to manage the execution of Node processes """
    _daemons: dict[int, Any]
    _node_cmd: str = "/usr/bin/node"

    def __init__(self):
        self._daemons = {}
        self._node_cmd = shutil.which('node')  # Try to discover full path of node command

    @classmethod
    async def read_stream(cls, proc, stream, callback: Callable[[str], None]) -> None:
        """
        Reads the stout/stderr stream of a given process
        :param proc: the process to read the output from
        :param stream: the stdout stream
        :param callback: a function to call on each line read from the stream
        :return: None
        """
        while proc.returncode is None:
            data = await stream.readline()
            if not data:
                break
            callback(data.decode().rstrip())

    @contextlib.asynccontextmanager
    async def open_process(self, cmd: str, *cmd_args: dict[str, str], work_dir: str = None,
                           env_vars: dict[str, str] = None, daemon: bool = False,
                           stdout_callback: Callable[[str], None] = print) -> None:
        """
        Creates a new Node process

        :param cmd: the command to execute
        :param cmd_args: the command arguments
        :param work_dir: the path to the working directory
        :param env_vars: the environment variables to set
        :param daemon: True if the process will run as a daemon
        :param stdout_callback: the callback function to call when reading the output stream
        :return: None
        """
        proc = await asyncio.create_subprocess_exec(
            cmd, *cmd_args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=work_dir, env=env_vars
        )
        stream_task = asyncio.create_task(self.read_stream(proc,
                                                           proc.stdout,
                                                           stdout_callback))

        async def server_wait():
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
                except asyncio.exceptions.TimeoutError:
                    pass

    async def execute(self, js_file: str = None, port: int = None,
                      stdout_callback: Callable[[str], None] = partial(print, flush=True)) -> None:
        """
        Use Node.js to run the provided script. If a port is given,
        the script will be run as a daemon
        :param js_file: the full path to the JavaScript file
        :param port: the port number
        :param stdout_callback: the callback function to call when reading the output stream
        :return: None
        """
        server_env = environ.copy()
        if port:
            self.kill_daemon(port)   # Kill any Node process using the port
            server_env["NODE_PORT"] = str(port)

        work_dir = path.dirname(path.realpath(js_file))
        daemon = port is not None
        async with self.open_process(self._node_cmd, js_file,
                                     work_dir=work_dir,
                                     env_vars=server_env, daemon=daemon,
                                     stdout_callback=stdout_callback) as proc:
            if daemon:
                self._daemons[port] = proc

    @classmethod
    def _force_kill(cls, port):
        """ To kill a Node.js process listening on a given port """
        for proc in psutil.process_iter(['pid', 'name', 'connections']):
            try:
                for conn in proc.connections():
                    if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
                        print(f"Killing existing {proc.name()} process, id {proc.pid} "
                              f"and listening on port {port}", flush=True)
                        proc.kill()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

    def kill_daemon(self, port) -> None:
        """
        Kills a previously started daemon process
        :param port: the port the daemon is likely listening to
        :return: None
        """
        if port in self._daemons:
            process = self._daemons[port]
            try:
                process.kill()
            except ProcessLookupError:
                print(f"No node process on port {port}, ok to continue...")
        else:
            self._force_kill(port)

    def __del__(self):
        """ Some cleanup during testing and extension unloading """
        for proc in self._daemons.values():
            try:
                proc.terminate()
            except ProcessLookupError as e:
                print(f"Error: process not found {e}")


# This code JavaScript will be included with the cell's code to
# redirect the output of calls to console.[log, error, warn] to the
# result section of the cell
_cell_console = """
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


class JavascriptWithConsole(Javascript):
    """
    This class extends JavaScript to intercept calls to console.log
    and make a result section of the cell.
    """

    CELL_CONSOLE: str = _cell_console

    def __init__(self, data=None, url=None, filename=None, lib=None, css=None):
        super().__init__(data=data, url=url, filename=filename, lib=lib, css=None)

    def _repr_javascript_(self):
        return self.CELL_CONSOLE + super()._repr_javascript_()


@magics_class
class NodeMagics(DisplayMagics):
    _arg_parser: ArgumentParser
    _proc_mgmt: NodeProcessManager
    _in_notebook: bool

    def __init__(self, shell):
        super().__init__(shell=shell)
        self._arg_parser = self._create_parser()
        self._proc_mgmt = NodeProcessManager()
        self._in_notebook = shell.has_trait('kernel')

    @classmethod
    def _create_parser(cls) -> ArgumentParser:
        parser = ArgumentParser()
        parser.add_argument("-t", "--target", type=str,
                            choices=['browser', 'node', 'disk'], default="browser",
                            help="the target for script execution")
        parser.add_argument("-f", "--filename", type=str,
                            help="filename when cell contents are saved to disk")
        parser.add_argument("-p", "--port", type=int,
                            help="a port number if the cell starts a Node server process")
        return parser

    @classmethod
    def _save_script(cls, filename: str, cell_content: str) -> str:
        """ Create the JavaScript file for Node to run """
        if not filename:
            filename = f"{uuid.uuid4().hex}.js"
        with io.open(filename, 'w', encoding='utf-8') as f:
            f.write(cell_content)
        return filename

    def _run_on_node(self, js_file: str, port: int = None) -> None:
        if self._in_notebook:
            loop = asyncio.get_event_loop()
            loop.create_task(self._proc_mgmt.execute(js_file, port))
        else:
            asyncio.run(self._proc_mgmt.execute(js_file, port))

    @cell_magic
    def javascript(self, line=None, cell=None):
        args = self._arg_parser.parse_args(line.split() if line else "")

        if args.target == 'node':
            if not args.filename:
                raise ValueError(
                    "--filename is required when using --target=node"
                )
            js_file = self._save_script(args.filename, cell)
            self._run_on_node(js_file, args.port)
        elif args.target == 'browser':
            display(JavascriptWithConsole(cell))
        elif args.target == 'disk':
            if not args.filename:
                raise ValueError(
                    "--filename is required when using --target=disk"
                )
            self._save_script(args.filename, cell)


def load_ipython_extension(ipython):
    """
    Loads the ipython extension
    :param ipython: The currently active `InteractiveShell` instance.
    :return: None
    """
    try:
        node_magic = NodeMagics(ipython)
        ipython.register_magics(node_magic)
        ipython.node_magic = node_magic
    except NameError:
        print("IPython shell not available.")


# Check if the module has not been loaded with %load_ext
if '__IPYTHON__' not in globals():
    load_ipython_extension(get_ipython())
