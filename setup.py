#!/usr/bin/env python
import os
from setuptools import setup, Command


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


setup(
    name='pytest-bdd',
    description='BDD for pytest',
    author='Oleg Pidsadnyi, Anatoly Bubenkov',
    version='0.1',
    cmdclass={'test': PyTest},
    install_requires=[
        'pytest',
    ],
    tests_require=['mock'],
    packages=['pytest_bdd'],
)
