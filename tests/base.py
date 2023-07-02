#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
from IPython.testing.globalipapp import get_ipython
from IPython.core.displaypub import DisplayPublisher
from typing import Any
import logging


class BaseTestCase(unittest.TestCase):
    """ Base testcase for all tests """
    ipython = None
    publisher = None
    previous_pub = None
    log_handler = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    def setUpClass(cls) -> None:
        print("Setting up IPython...")
        cls.ipython = get_ipython()
        cls.ipython.log.setLevel(logging.DEBUG)
        cls.log_handler = logging.StreamHandler()
        cls.ipython.log.addHandler(cls.log_handler)
        # To be able to intercept the calls to display()
        cls.previous_pub = cls.ipython.display_pub
        cls.publisher = CaptureDisplayPub(cls.ipython.display_pub)
        cls.ipython.display_pub = cls.publisher

    @classmethod
    def tearDownClass(cls) -> None:
        print("Cleaning up...")
        cls.publisher = cls.previous_pub
        cls.ipython.log.removeHandler(cls.log_handler)


class CaptureDisplayPub(DisplayPublisher):
    """
    Used during testing for capturing the calls to
    display() by the extensions.
    """

    def __init__(self, shell=None):
        super().__init__(shell=shell)
        self._display_output: list[dict[str, Any]] = []

    def publish(self, data, **kwargs):
        self._display_output.append(data)

    def delete_output(self):
        self._display_output.clear()

    @property
    def display_output(self):
        return self._display_output
