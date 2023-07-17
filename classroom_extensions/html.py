#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" IPython magics to make the result section of
a cell mimic the browser's console """

from argparse import ArgumentParser
from typing import AnyStr
from IPython.core.magic import magics_class, cell_magic
from IPython.core.magics.display import DisplayMagics
from IPython.display import display, HTML
from .node import JavascriptWithConsole


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
            html += (
                f"<script>{_CONSOLE_TITLE}{JavascriptWithConsole.CELL_CONSOLE}</script>"
            )
        return html + super()._repr_html_()


@magics_class
class HTMLMagics(DisplayMagics):
    """Provides the html magics"""

    _arg_parser: ArgumentParser
    _in_notebook: bool

    def __init__(self, shell):
        super().__init__(shell=shell)
        self._arg_parser = self._create_parser()
        self._in_notebook = shell.has_trait("kernel")

    @classmethod
    def _create_parser(cls) -> ArgumentParser:
        parser = ArgumentParser()
        parser.add_argument(
            "-c",
            "--console",
            action="store_true",
            help="Whether to display a copy of the browser's console or not",
        )
        return parser

    @cell_magic
    def html(self, line=None, cell=None) -> None:
        args = self._arg_parser.parse_args(line.split() if line else "")
        html = HTMLWithConsole(cell, args.console)
        display(html)


def load_ipython_extension(ipython) -> None:
    """
     Loads the ipython extension

    Args:
        ipython (InteractiveShell): Currently active `InteractiveShell` instance.

    Returns:
        None
    """
    try:
        html_magic = HTMLMagics(ipython)
        ipython.register_magics(html_magic)
        ipython.html_magic = html_magic
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
        del ipython.html_magic
    except (NameError, AttributeError):
        print("IPython shell not available.")
