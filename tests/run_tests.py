#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from IPython.testing.globalipapp import start_ipython

# To make sure IPython is available for all tests
start_ipython()

from .test_html import TestHTML
from .test_mariadb import TestMariaDB
from .test_plantuml import TestPlantUML
from .test_nodejs import TestNodeJs

# test_suite = unittest.TestSuite()

# test_suite.addTest(unittest.makeSuite(TestHTML))
# test_suite.addTest(unittest.makeSuite(TestMariaDB))
# test_suite.addTest(unittest.makeSuite(TestPlantUML))
# test_suite.addTest(unittest.makeSuite(TestNodeJs))

# test_runner = unittest.TextTestRunner()
# test_runner.run(test_suite)

