#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
An extension to create the %%sql magic command using the MariaDB kernel to
execute the commands using the CLI client. Although it uses the MariaDB kernel, using it as
an extension does not limit the notebook to executing only SQL commands. This assumes you have

Note: MariaDB server and client installed, and that you have created a MariaDB kernel
configuration file before loading this extension.
"""
from IPython.core.magic import magics_class, cell_magic
from IPython.core.magics.display import DisplayMagics
from IPython.display import display, HTML
from mariadb_kernel.code_parser import CodeParser
from mariadb_kernel.mariadb_client import MariaDBClient, ServerIsDownError
from mariadb_kernel.client_config import ClientConfig


@magics_class
class MariaDBMagics(DisplayMagics):
    """Implements the MariaDB magics using the database
    client provided by the MariaDB kernel"""

    db_client: MariaDBClient
    in_notebook: bool

    def __init__(self, shell):
        super().__init__(shell=shell)
        self.in_notebook = shell.has_trait("kernel")
        self.log = shell.log
        config = ClientConfig(self.log)
        self.db_client = MariaDBClient(self.log, config)
        self.db_client.start()

    def __del__(self):
        self.db_client.stop()

    @cell_magic
    def sql(self, line="", cell=None) -> None:
        """
        Code to intercept the SQL code and execute it using MariaDB iPython kernel.

        Args:
            line: (str) Not used, included to avoid error
            cell: (str) The contents of the cell to execute

        Returns:
            None
        """
        parser: CodeParser
        try:
            parser = CodeParser(self.log, cell, ";")
        except ValueError as value_error:
            self.log.error(f"Error with SQL parser: {str(value_error)}")
            return

        result = ""
        for stmt in parser.get_sql():
            result += self.db_client.run_statement(stmt)

            if self.db_client.iserror():
                self.log.error(f"Error: {self.db_client.error_message()}")
                continue

        display_obj = HTML(result) if self.in_notebook else result
        display(display_obj)


def load_ipython_extension(ipython):
    """
    Loads the ipython extension

    Args:
        ipython: (InteractiveShell) The currently active `InteractiveShell` instance.

    Returns:
        None
    """
    try:
        ipython.register_magics(MariaDBMagics(ipython))
    except ServerIsDownError as server_error:
        ipython.log.error(f"Error trying to access MariaDB Server: {server_error}")
    except NameError as name_error:
        ipython.log.error(f"Error registering the magic command: {name_error}")
