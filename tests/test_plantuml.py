#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Tests the PlantUML magics """

import unittest
from classroom_extensions.plantuml import PlantUmlMagics
from .base import BaseTestCase


class TestPlantUML(BaseTestCase):
    """Testcase for the PlantUML extension"""

    def test_config(self):
        """Tests creating a config file"""
        print("Testing PlantUML config...")
        magics1 = PlantUmlMagics(shell=self.ipython)
        previous_server = magics1.plantweb_config["server"]
        magics1.plantuml_config("--server=http://localhost:8080/plantuml/")
        magics2 = PlantUmlMagics(shell=self.ipython)
        self.assertEqual(
            "http://localhost:8080/plantuml/", magics2.plantweb_config["server"]
        )
        magics2.plantuml_config(f"--server={previous_server}")

    def test_render_svg(self):
        """Tests rendering an svg"""
        print("Testing PlantUML rendering SVG...")
        content = """
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
        magics = PlantUmlMagics(shell=self.ipython)
        try:
            magics.plantuml(cell=content)
        except Exception as exception:
            self.fail(f"Error: {exception}")

    def test_render_png(self):
        """Tests rendering a png"""
        print("Testing PlantUML rendering PNG...")
        content = """
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
        magics = PlantUmlMagics(shell=self.ipython)
        try:
            magics.plantuml(cell=content)
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
        unload = self.ipython.extension_manager.unload_extension(
            "classroom_extensions.plantuml"
        )
        self.assertEqual(unload, "no unload function")


if __name__ == "__main__":
    unittest.main()
