#!/usr/bin/env python
import os
from setuptools import setup, find_packages

packages = find_packages(os.path.dirname(os.path.abspath(__file__)))

setup(
    name='pytest-bdd',
    description='BDD for pytest',
    version='0.1',
    install_requires=[
        'pytest',
        'splinter',
    ],
    packages=packages,
)
