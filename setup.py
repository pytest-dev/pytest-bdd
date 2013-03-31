#!/usr/bin/env python

from setuptools import setup

setup(
    name='pytestbdd',
    description='BDD for pytest',
    version='0.1',
    install_requires=[
        'pytest',
        'splinter',
    ],
    packages=['pytestbdd'],
)
