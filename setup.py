#!/usr/bin/env python
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='pytest-bdd',
    description='BDD for pytest',
    author='Oleg Pidsadnyi',
    author_email='oleg.podsadny@gmail.com',
    version='0.4.1',
    cmdclass={'test': PyTest},
    install_requires=[
        'pytest',
    ],
    # the following makes a plugin available to py.test
    entry_points = {
        'pytest11': [
            'pytest-bdd = pytest_bdd.plugin',
        ]
    },
    tests_require=['mock'],
    packages=['pytest_bdd'],
)
