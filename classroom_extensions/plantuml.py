#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Extension that uses PlantUML to draw multiple types of diagrams """

from copy import copy
from os.path import expanduser, exists
import json
import sys
from plantweb.render import render
from IPython.core.magic import magics_class, cell_magic, line_magic
from IPython.core.magics.display import DisplayMagics, display
from IPython.display import SVG, Image
from IPython.core import magic_arguments
from IPython.utils.process import arg_split

__all__ = ["load_ipython_extension", "PlantUmlMagics"]


DEFAULT_PLANTWEB_CONFIG = {
    "engine": "plantuml",
    "format": "svg",
    "server": "http://plantuml.com/plantuml/",
    "use_cache": True,
    "cache_dir": "~/.cache/plantweb",
}


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
        self._plantweb_config = self._load_plantweb_config()

    @property
    def plantweb_config(self) -> dict:
        """Returns the plantweb configuration"""
        return self._plantweb_config

    def _load_plantweb_config(self) -> dict:
        if not exists(self._config_path):
            return copy(DEFAULT_PLANTWEB_CONFIG)
        with open(self._config_path, "r", encoding="utf-8") as config_file:
            return dict(json.loads(config_file.read()))

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

        output, out_format, _, _ = render(
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
            self._save_plantuml_config()
        else:
            print(
                "Use --server=address to provide the address of a valid PlantUML server"
            )


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
        ipython.node_magic = uml_magics
    except NameError:
        print("IPython shell not available.")
