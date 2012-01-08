from distutils.core import setup
from distutils.cmd import Command
from unittest import TextTestRunner, TestLoader
import tests

cmdclasses = dict()

class TestCommand(Command):
    """Runs the unit tests for mymodule"""

    user_options = []
    def initialize_options(self):
        pass
    def finalize_options(self):
        pass
    def run(self):
        loader = TestLoader()
        t = TextTestRunner()
        t.run(loader.loadTestsFromModule(tests))
#        t.run(unittest.TestLoader().loadTestsFromTestCase(tests.SanityCheck))

# 'test' is the parameter as it gets added to setup.py
cmdclasses['test'] = TestCommand

setup(
    name = "dago",
    packages = ["dago"],
    version = "0.0.1",
    description = "Dago - A Python Collection",
    author = "Derrick Petzold",
    author_email = "dago@derrickpetzold.com",
    url = "http://derrickpetzold.com/dago",
    download_url = "http://media.derrickpetzold.com/dago-0.0.1.tgz",
    keywords = ['django'],
    cmdclass = cmdclasses,
)
