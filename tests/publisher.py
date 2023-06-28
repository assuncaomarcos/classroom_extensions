#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Used during testing for capturing the calls to
display() by the extensions.
"""
from IPython.core.displaypub import DisplayPublisher
from typing import Any


class CaptureDisplayPub(DisplayPublisher):
    _display_output: list[dict[str, Any]] = []

    def __init__(self, shell=None):
        super().__init__(shell=shell)

    def publish(self, data, **kwargs):
        self._display_output.append(data)

    def delete_output(self):
        self._display_output.clear()

    @property
    def display_output(self):
        return self._display_output
