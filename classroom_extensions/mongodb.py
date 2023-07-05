#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Used to run commands on the MongoDB shell """

from IPython.core.magic import (magics_class, cell_magic, line_magic)
from IPython.core.magics.display import DisplayMagics
from IPython.core.magics.script import ScriptMagics
from IPython.core import magic_arguments
from IPython.utils.process import arg_split
from argparse import Namespace
from os import environ, path
import json
import shutil
import sys


def mongosh_args(f):
    """Single decorator for adding mongosh args"""
    args = [
        magic_arguments.argument('--host',
                                 help='The hostname or IP address of the MongoDB server'),
        magic_arguments.argument('--port', type=int,
                                 help='The port number on which the MongoDB server is listening'),
        magic_arguments.argument('--username', help='The username for authentication'),
        magic_arguments.argument('--password', help='The password for authentication'),
        magic_arguments.argument('--authenticationDatabase',
                                 help='The database used for authentication'),
        magic_arguments.argument('--tls', action='store_true',
                                 help='Enable TLS/SSL for the connection'),
        magic_arguments.argument('--tlsCAFile', type=open,
                                 help='The path to the CA certificate file'),
        magic_arguments.argument('--tlsCertificateKeyFile', type=open,
                                 help='The path to the client certificate and private key file')
    ]
    for arg in args:
        f = arg(f)
    return f


class MongoDBConfig:
    """ To keep the configuration on how to connect to MongoDB """

    def __init__(self, config_file: str = "mongodb_extension.json"):
        self._config_file = config_file
        self._config = {
            'host': 'localhost',
            'port': 27017,
            'username': None,
            'password': None,
            'authenticationDatabase': None,
            'tls': False,
            'tlsCAFile': None,
            'tlsCertificateKeyFile': None
        }
        self._load_config()

    def update_config(self, config: dict = None) -> None:
        """
        Updates the configuration with the
        values in the provided dictionary

        :param: config a dictionary of configuration parameters
        """
        self._config.update(config)

    def _load_config(self):
        config_path = self._config_path()
        if path.exists(config_path):
            with open(config_path, 'r') as fd:
                try:
                    self._config.update(json.loads(fd.read()))
                except json.JSONDecodeError as de:
                    print(f"Error reading MongoDB config: {de}")

    def _config_path(self):
        default_dir = path.join(path.expanduser("~"), ".jupyter")
        custom_dir = environ.get("JUPYTER_CONFIG_DIR")
        if custom_dir:
            default_dir = custom_dir
        return path.join(default_dir, self._config_file)

    def save(self) -> None:
        """ Saves the configuration into the config file """
        config_path = self._config_path()
        with open(config_path, 'w', encoding="utf-8") as fd:
            fd.write(json.dumps(self._config))

    def get_shell_args(self, args: dict = None) -> str:
        """ Returns a list of arguments a mongosh command line """
        command = ""
        arg_list = args if args else self._config
        for arg, value in arg_list.items():
            if value is not None:
                if isinstance(value, bool):
                    if value:
                        command += f' --{arg}'
                else:
                    command += f' --{arg} {value}'

        return command

    def copy(self):
        clone = MongoDBConfig(self._config_file)
        clone.update_config(self._config)
        return clone


@magics_class
class MongoDBMagics(DisplayMagics):
    """ Defines the mongo shell magics """
    _config: MongoDBConfig = MongoDBConfig()
    _script_magics: ScriptMagics

    def __init__(self, shell=None):
        super().__init__(shell=shell)
        self.log = shell.log
        self._mongosh = self._shell_path()
        self._script_magics = ScriptMagics(shell=shell)

    def _shell_path(self) -> str:
        shell_path = shutil.which('mongosh')
        if shell_path:
            return shell_path
        else:
            self.log.error("Command mongosh not found.")
            raise FileNotFoundError(
                "Error: mongosh not found. Please install mongosh"
            )

    @magic_arguments.magic_arguments()
    @mongosh_args
    @cell_magic
    def mongo(self, line="", cell=None):
        # Check whether the user provided mongosh parameters with the cell
        argv = arg_split(line, posix=not sys.platform.startswith("win"))
        args = self.mongo.parser.parse_args(argv)
        config = self._config.copy()
        config.update_config(vars(args))

        # The flow here is not sophisticated. We simply leverage the
        # ScriptMagics' script that creates a process, writes the cell
        # contents to its stdin and creates stream readers that read from
        # stdout and stderr to render the execution results
        try:
            params = f"--quiet --no-raise-error {config.get_shell_args()}"
            cmd = f"{self._mongosh} {params}"
            self._script_magics.shebang(line=cmd, cell=cell.strip())
        except Exception as e:
            print(f"Error while executing mongosh: {e}")

        #TODO: By default, ScriptMagics.shebang does not echo the
        # stdin to stdout. Find an alternative to it.

    def _set_config(self, args: Namespace):
        new_config = {}
        for arg, value in vars(args).items():
            if value:
                new_config[arg] = value

        self._config.update_config(new_config)

    @magic_arguments.magic_arguments()
    @mongosh_args
    @line_magic
    def mongo_config(self, line=None):
        argv = arg_split(line, posix=not sys.platform.startswith("win"))
        args = self.mongo_config.parser.parse_args(argv)
        self._set_config(args)
        self._config.save()


def load_ipython_extension(ipython):
    """
    Loads the ipython extension
    :param ipython: The currently active `InteractiveShell` instance.
    :return: None
    """
    try:
        mongo_magics = MongoDBMagics(ipython)
        ipython.register_magics(mongo_magics)
        ipython.mongo_magics = mongo_magics
    except NameError:
        print("IPython shell not available.")


def unload_ipython_extension(ipython):
    """ Does some clean up """
    del ipython.mongo_magics
