#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Extension that uses PlantUML to draw multiple types of diagrams """

import json
import sys
from os.path import expanduser

from IPython.core import magic_arguments
from IPython.core.magic import magics_class, cell_magic, line_magic, line_cell_magic
from IPython.core.magics.display import DisplayMagics, display
from IPython.display import SVG, Image
from IPython.utils.process import arg_split
from plantweb import render, defaults

__all__ = ["load_ipython_extension", "unload_ipython_extension", "PlantUmlMagics"]

DEFAULT_PLANTWEB_CONFIG = defaults.DEFAULT_CONFIG


def plantuml_args(func):
    """Single decorator for adding plantuml args"""
    args = [
        magic_arguments.argument(
            "-s", "--server", help="Address of the PlantUML server to use"
        ),
        magic_arguments.argument(
            "-f",
            "--format",
            choices=["svg", "png"],
            default="svg",
            help="The output format to used",
        ),
    ]
    for arg in args:
        func = arg(func)
    return func


@magics_class
class PlantUmlMagics(DisplayMagics):
    """
    Implements magics for using PlantUML and enabling creating
    several types of diagrams in Jupyter notebooks
    """

    _config_path: str = expanduser("~/.plantwebrc")
    """ The default path of the config file """

    def __init__(self, shell=None):
        super().__init__(shell=shell)
        self._plantweb_config = defaults.read_defaults()

    @property
    def plantweb_config(self) -> dict:
        """Returns the plantweb configuration"""
        return self._plantweb_config

    def _save_plantuml_config(self) -> None:
        with open(self._config_path, "w", encoding="utf-8") as config_file:
            config_file.write(json.dumps(self._plantweb_config))

    @magic_arguments.magic_arguments()
    @plantuml_args
    @cell_magic("plantuml")
    def plantuml(self, line: str = "", cell: str = None):
        """Cell magic responsible for rendering the SVG/PNG diagram"""
        argv = arg_split(line, posix=not sys.platform.startswith("win"))
        args = self.plantuml.parser.parse_args(argv)
        server = args.server if args.server else self._plantweb_config["server"]

        output, out_format, _, _ = render.render(
            cell, server=server, engine="plantuml", format=args.format
        )
        if out_format == "svg":
            svg = SVG(data=output)
            display(svg)
        else:
            img = Image(data=output)
            display(img)

    @magic_arguments.magic_arguments()
    @plantuml_args
    @line_magic
    def plantuml_config(self, line=None) -> None:
        """
        Used to set the server address in case one
        wants to use its local PlatUML server
        """
        argv = arg_split(line, posix=not sys.platform.startswith("win"))
        args = self.plantuml_config.parser.parse_args(argv)

        if args.server:
            self._plantweb_config["server"] = args.server
        else:
            print(
                "Use --server=address to provide the address of a valid PlantUML server"
            )

        self._plantweb_config["format"] = args.format
        self._save_plantuml_config()

    @magic_arguments.magic_arguments()
    @plantuml_args
    @magic_arguments.argument("--json", "-j", type=str, help="Path to the file on disk")
    @line_cell_magic
    def json(self, line="", cell=None) -> None:
        """Used to create a graphical representation of a JSON file/object"""
        args = magic_arguments.parse_argstring(self.json, line)

        if args.json is not None:
            with open(args.json, "r", encoding="UTF-8") as json_file:
                cell = json_file.read()

        cell = f"""
                @startjson
                {cell}
                @endjson
                """
        command = ""
        for arg, value in vars(args).items():
            if value is not None and arg != "json":
                command += f" --{arg}={value}"

        self.plantuml(line=command, cell=cell)


def load_ipython_extension(ipython) -> None:
    """
    To unload the extension
    Args:
        ipython: the current interactive shell

    Returns:
        None
    """
    try:
        uml_magics = PlantUmlMagics(ipython)
        ipython.register_magics(uml_magics)
        ipython.plantuml_magics = uml_magics
    except (NameError, AttributeError):
        print("IPython shell not available.")


def unload_ipython_extension(ipython) -> None:
    """
    To unload the extension

    Args:
        ipython (InteractiveShell): Currently active `InteractiveShell` instance.

    Returns:
        None
    """
    try:
        del ipython.plantuml_magics
    except (NameError, AttributeError):
        print("IPython shell not available.")
