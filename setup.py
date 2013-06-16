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

long_description = open('README.md').read()

setup(
    name='pytest-bdd',
    description='BDD for pytest',
    long_description=long_description,
    author='Oleg Pidsadnyi',
    license='MIT license',
    author_email='oleg.podsadny@gmail.com',
    version='0.4.2',
    classifiers=[
        'Development Status :: 6 - Mature',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: MacOS :: MacOS X',
        'Topic :: Software Development :: Testing',
        'Topic :: Software Development :: Libraries',
        'Topic :: Utilities',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3'
    ] + [('Programming Language :: Python :: %s' % x) for x in '2.6 2.7 3.0 3.1 3.2 3.3'.split()],
    cmdclass={'test': PyTest},
    install_requires=[
        'pytest',
    ],
    # the following makes a plugin available to py.test
    entry_points={
        'pytest11': [
            'pytest-bdd = pytest_bdd.plugin',
        ]
    },
    tests_require=['mock'],
    packages=['pytest_bdd'],
)
