#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Extension that uses PlantUML to draw multiple types of diagrams """

from IPython.core.magic import (magics_class, cell_magic, line_magic)
from IPython.core.magics.display import DisplayMagics, display
from IPython.core.getipython import get_ipython
from IPython.display import SVG, Image
from argparse import ArgumentParser
from copy import copy
from os.path import expanduser, exists
from plantweb.render import render
import json

__all__ = [
    "load_ipython_extension",
    "PlantUmlMagics"
]


DEFAULT_PLANTWEB_CONFIG = {
    'engine': 'plantuml',
    'format': 'svg',
    'server': 'http://plantuml.com/plantuml/',
    'use_cache': True,
    'cache_dir': '~/.cache/plantweb'
}


@magics_class
class PlantUmlMagics(DisplayMagics):
    _config_path: str = expanduser("~/.plantwebrc")

    def __init__(self, shell=None):
        super().__init__(shell=shell)
        self._plantweb_config = self._load_plantweb_config()

    @property
    def plantweb_config(self):
        return self._plantweb_config

    def _load_plantweb_config(self) -> dict:
        if not exists(self._config_path):
            return copy(DEFAULT_PLANTWEB_CONFIG)
        with open(self._config_path, 'r') as fd:
            return dict(json.loads(fd.read()))

    def _save_plantuml_config(self) -> None:
        with open(self._config_path, 'w') as fd:
            fd.write(json.dumps(self._plantweb_config))

    @cell_magic
    def plantuml(self, line=None, cell=None):
        """ Cell magic responsible for rendering the SVG/PNG diagram """
        output, out_format, _, _ = render(
            cell,
            engine='plantuml',
            format='svg'
        )
        if out_format == 'svg':
            svg = SVG(data=output)
            display(svg)
        else:
            img = Image(data=output)
            display(img)

    @line_magic
    def plantuml_config(self, line=None):
        """ Used to set the server address in case one wants to use its local PlatUML server """
        parser = ArgumentParser()
        parser.add_argument("-s", "--server", type=str, help="Address of the PlantUML server to use")
        args = parser.parse_args(line.split() if line else "")
        if args.server:
            self._plantweb_config['server'] = args.server
            self._save_plantuml_config()
        else:
            print("Use --server=address to provide the address of a valid PlantUML server")


def load_ipython_extension(ipython):
    """
    Loads the ipython extension
    :param ipython: The currently active `InteractiveShell` instance.
    :return: None
    """
    try:
        uml_magics = PlantUmlMagics(ipython)
        ipython.register_magics(uml_magics)
        ipython.node_magic = uml_magics
    except NameError:
        print("IPython shell not available.")


# Check if the module has not been loaded with %load_ext
if '__IPYTHON__' not in globals():
    load_ipython_extension(get_ipython())
