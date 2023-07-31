.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/psf/black
.. image:: https://coveralls.io/repos/github/assuncaomarcos/classroom_extensions/badge.svg?branch=main
    :target: https://coveralls.io/github/assuncaomarcos/classroom_extensions?branch=main


IPython Extensions for Teaching
===============================

This project provides a set of IPython extensions used for teaching at the
Ecole de Technologie Superieure (ETS) of Montreal. The extensions work on
Google Colab, and Jupyter notebooks with some effort, and provide a set of
magics (e.g., `%%sql`) while customizing existing ones (e.g., `%%javascript`)
to enable lecturers and students to deploy software frameworks quickly and
provide notes with working examples.

The `notebooks` directory contains a set of Google Colab examples of how to
use the IPython extensions.

Installing the Extensions
-------------------------

You can use `pip` to install the extensions:

.. code-block::

    pip3 install classroom-extensions

or:

.. code-block::

    pip3 install git+https://github.com/assuncaomarcos/classroom_extensions.git

Or clone this git repository and load the required extensions from the `classroom_extensions` package.

MariaDB Magics
--------------

Two extensions are available for MariaDB. One extension (`mariadb`) uses some
components of the MariaDB Jupyter Kernel and creates a `%%sql` cell magic that enables
code cells to accept SQL commands that an instance of MariaDB interprets. However,
unlike the MariaDB Jupyter Kernel, this extension does not change the IPython kernel
and its magics, hence enabling one to continue coding in Python, JavaScript, etc.
To ease the creation of notebooks on Google Colab, a second extension (`mariadb_install`)
installs MariaDB and the required libraries to run the first extension without
worrying about setting things up.

Server-Side JavaScript
----------------------

This extension, called `web`, customizes the `%%javascript` cell magic to enable
executing JavaScript code on the server or container hosting the Jupyter Notebook or
on Google Colab. Node.js executes the code provided in a cell whose `--target` argument
receives the value `web`. It also enables starting long-running Node.js server
processes that will listen on given ports without blocking the code cell of
the notebook. In addition to executing JavaScript code on the server side, when run
on the browser, the magic enables printing the output of the browser's console in
the result section of the code cell.

Custom HTML Magic
-----------------

The `web` extension also customizes the `%%html` magic. After rendering the HTML code
inserted in the cell, the extension displays a high-level copy of the browser's
console. This behavior helps in teaching HTML or JavaScript that writes on the console.

PlantUML Magics
---------------

PlantUML is a textual Domain-Specific Language (DSL) used for creating diagrams,
primarily focused on software engineering and system design. It allows you to
express diagrams using a simple and intuitive syntax, which PlantUML transforms into
various types of visual diagrams, such as Unified Modeling Language (UML), sequence,
class, activity, and more.

MongoDB Shell Magics
--------------------

The IPython extension `%%mongo` enables seamless interaction with MongoDB using
the `mongosh` CLI. By simply prefixing a cell with `%%mongo`, users can execute queries
and commands against a MongoDB database directly within their IPython environment
or Colab. The extension leverages the power of the `mongosh` CLI to provide a simple
and familiar MongoDB Shell experience, allowing for data exploration, manipulation,
and administration tasks.
