#!/usr/bin/env python
"""pytest-bdd package config."""

import codecs
import os
import re

from setuptools import setup


dirname = os.path.dirname(__file__)

long_description = (
    codecs.open(os.path.join(dirname, "README.rst"), encoding="utf-8").read()
    + "\n"
    + codecs.open(os.path.join(dirname, "AUTHORS.rst"), encoding="utf-8").read()
)

with codecs.open(os.path.join(dirname, "pytest_bdd", "__init__.py"), encoding="utf-8") as fd:
    VERSION = re.compile(r".*__version__ = ['\"](.*?)['\"]", re.S).match(fd.read()).group(1)

setup(
    name="pytest-bdd",
    description="BDD for pytest",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    author="Oleg Pidsadnyi, Anatoly Bubenkov and others",
    license="MIT license",
    author_email="oleg.pidsadnyi@gmail.com",
    url="https://github.com/pytest-dev/pytest-bdd",
    version=VERSION,
    classifiers=[
        "Development Status :: 6 - Mature",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS :: MacOS X",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries",
        "Topic :: Utilities",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ]
    + [("Programming Language :: Python :: %s" % x) for x in "2.7 3.5 3.6 3.7 3.8".split()],
    install_requires=["glob2", "Mako", "parse", "parse_type", "py", "pytest>=4.3", "six>=1.9.0"],
    # the following makes a plugin available to py.test
    entry_points={
        "pytest11": ["pytest-bdd = pytest_bdd.plugin"],
        "console_scripts": ["pytest-bdd = pytest_bdd.scripts:main"],
    },
    tests_require=["tox"],
    packages=["pytest_bdd"],
    include_package_data=True,
)
