from distutils.core import setup

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
