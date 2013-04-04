#!/usr/bin/env python
import os
from setuptools import setup, Command, find_packages


class PyTest(Command):
    """Testing."""
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess
        errno = subprocess.call([sys.executable, '-m', 'pytest'])
        raise SystemExit(errno)

packages = find_packages(os.path.dirname(os.path.abspath(__file__)))

setup(
    name='pytest-bdd',
    description='BDD for pytest',
    version='0.1',
    cmdclass={'test': PyTest},
    install_requires=[
        'pytest',
    ],
    tests_require=['mock'],
    packages=packages,
)
