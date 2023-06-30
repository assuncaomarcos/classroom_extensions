
import unittest
from IPython.testing.globalipapp import get_ipython
import logging


class TestNodeJs(unittest.TestCase):
    """ Testcase for the NodeJs extension """

    @classmethod
    def setUpClass(cls) -> None:
        cls.ipython = get_ipython()

    def setUp(self) -> None:
        self.ipython.log.setLevel(logging.DEBUG)
        self.ipython.log.addHandler(logging.StreamHandler())

    def test_config(self):
        from classroom_extensions.plantuml import PlantUmlMagics
        magics1 = PlantUmlMagics(shell=self.ipython)
        previous_server = magics1.plantweb_config['server']
        magics1.plantuml_config("--server=http://localhost:8080/plantuml/")
        magics2 = PlantUmlMagics(shell=self.ipython)
        self.assertEqual("http://localhost:8080/plantuml/", magics2.plantweb_config['server'])
        magics2.plantuml_config(f"--server={previous_server}")

    def test_render(self):
        from classroom_extensions.plantuml import PlantUmlMagics
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
        magics.plantuml(cell=content)

    def test_load_extension(self):
        self.ipython.extension_manager.load_extension('classroom_extensions.plantuml')
        second_load = self.ipython.extension_manager.load_extension('classroom_extensions.plantuml')
        self.assertEqual(second_load, "already loaded")
        unload = self.ipython.extension_manager.unload_extension('classroom_extensions.plantuml')
        self.assertEqual(unload, "no unload function")


if __name__ == '__main__':
    unittest.main()