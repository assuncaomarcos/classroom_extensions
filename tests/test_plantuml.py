#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests the PlantUML magics """

import unittest
from contextlib import contextmanager
from classroom_extensions.plantuml import PlantUmlMagics
import classroom_extensions.plantuml as plantuml_ext
from .base import BaseTestCase

_AZURE_DIAGRAM = """
    @startuml
    !include <azure/AzureCommon>
    !include <azure/Analytics/AzureEventHub>
    !include <azure/Analytics/AzureStreamAnalyticsJob>
    !include <azure/Databases/AzureCosmosDb>

    left to right direction

    agent "Device Simulator" as devices #fff

    AzureEventHub(fareDataEventHub, "Fare Data", "PK: Medallion HackLicense VendorId; 3 TUs")
    AzureEventHub(tripDataEventHub, "Trip Data", "PK: Medallion HackLicense VendorId; 3 TUs")
    AzureStreamAnalyticsJob(streamAnalytics, "Stream Processing", "6 SUs")
    AzureCosmosDb(outputCosmosDb, "Output Database", "1,000 RUs")

    devices --> fareDataEventHub
    devices --> tripDataEventHub
    fareDataEventHub --> streamAnalytics
    tripDataEventHub --> streamAnalytics
    streamAnalytics --> outputCosmosDb
    @enduml
"""

_SIMPLE_DIAGRAM = """
    actor Foo1
    boundary Foo2
    control Foo3
    entity Foo4
    database Foo5
    Foo1 -> Foo2 : To boundary
    Foo1 -> Foo3 : To control
    Foo1 -> Foo4 : To entity
    Foo1 -> Foo5 : To database
"""

_SIMPLE_JSON = """
{
    "status": "OK",
    "code": 200,
    "total": 2,
    "data": [
        {
            "title": "Harum cumque placeat id.",
            "description": "Qui autem tenetur ut aut.",
            "url": "https://placekitten.com/300/500"
        },
        {
            "title": "Incidunt neque at enim fuga.",
            "description": "Harum libero quo dolorum aut vel.",
            "url": "https://placekitten.com/300/400"
        }
    ]
}
"""

_TEST_PLANTUML_URL = "http://localhost:8080/plantuml/"
_DEFAULT_PLANTUML_URL = "http://plantuml.com/plantuml/"
_DEFAULT_FORMAT = "svg"


class TestPlantUML(BaseTestCase):
    """Testcase for the PlantUML extension"""

    @contextmanager
    def _config(self, server, out_format):
        magics = PlantUmlMagics(shell=self.ipython)
        magics.plantuml_config(f"--server={server} --format={out_format}")
        yield magics
        magics.plantuml_config(
            f"--server={_DEFAULT_PLANTUML_URL} --format={_DEFAULT_FORMAT}"
        )

    def test_config(self):
        """Tests creating a config file"""
        print("Testing PlantUML config...")
        with self._config(server=_TEST_PLANTUML_URL, out_format="png") as magic:
            self.assertEqual(_TEST_PLANTUML_URL, magic.plantweb_config["server"])
            self.assertEqual("png", magic.plantweb_config.get("format"))
        with self._config(server=_TEST_PLANTUML_URL, out_format="svg") as magic:
            self.assertEqual(_TEST_PLANTUML_URL, magic.plantweb_config["server"])
            self.assertEqual("svg", magic.plantweb_config.get("format"))
        magic = PlantUmlMagics(self.ipython)
        output = self.capture_output(magic.plantuml_config, "--format=png")
        self.assertRegex(output, "Use --server=address to")

    def test_render_svg(self):
        """Tests rendering an svg"""
        print("Testing PlantUML rendering SVG...")
        with self._config(server=_DEFAULT_PLANTUML_URL, out_format="svg") as magic:
            try:
                magic.plantuml(cell=_SIMPLE_DIAGRAM)
            except Exception as exception:
                self.fail(f"Error: {exception}")

    def test_render_json(self):
        """Tests rendering an svg"""
        print("Testing PlantUML rendering JSON...")
        with self._config(server=_DEFAULT_PLANTUML_URL, out_format="png") as magic:
            try:
                magic.json(cell=_SIMPLE_JSON)
            except Exception as exception:
                self.fail(f"Error: {exception}")

        tmp_file = "/tmp/temp_json.json"
        with open(tmp_file, "w", encoding="UTF-8") as json_file:
            json_file.write(_SIMPLE_JSON)

        with self._config(server=_DEFAULT_PLANTUML_URL, out_format="png") as magic:
            try:
                magic.json(line=f"--json={tmp_file}", cell=None)
            except Exception as exception:
                self.fail(f"Error: {exception}")

    def test_render_png(self):
        """Tests rendering a png"""
        print("Testing PlantUML rendering PNG...")
        magic = PlantUmlMagics(self.ipython)
        magic.plantuml_config(f"--server={_DEFAULT_PLANTUML_URL}")
        try:
            magic.plantuml(line="--format=png", cell=_AZURE_DIAGRAM)
        except Exception as exception:
            self.fail(f"Error: {exception}")

    def test_load_extension(self):
        """Tests loading and unloading the extension"""
        print("Testing loading/unloading extension...")
        self.ipython.extension_manager.load_extension("classroom_extensions.plantuml")
        second_load = self.ipython.extension_manager.load_extension(
            "classroom_extensions.plantuml"
        )
        self.assertEqual(second_load, "already loaded")

    def test_incorrect_loading(self):
        """Tests incorrectly loading the extension."""
        expected = "IPython shell not available.\n"
        output = self.capture_output(plantuml_ext.load_ipython_extension, None)
        self.assertEqual(output, expected)
        output = self.capture_output(plantuml_ext.unload_ipython_extension, None)
        self.assertEqual(output, expected)


if __name__ == "__main__":
    unittest.main()
