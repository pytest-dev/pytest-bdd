"""pytest-bdd package config."""
import codecs
import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand

import pytest_bdd


class Tox(TestCommand):

    """"Custom setup.py test command implementation using tox runner."""

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--recreate -vv']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import detox.main
        errno = detox.main.main(self.test_args)
        sys.exit(errno)


dirname = os.path.dirname(__file__)

long_description = (
    codecs.open(os.path.join(dirname, 'README.rst'), encoding='utf-8').read() + '\n' +
    codecs.open(os.path.join(dirname, 'CHANGES.rst'), encoding='utf-8').read()
)

setup(
    name='pytest-bdd',
    description='BDD for pytest',
    long_description=long_description,
    author='Oleg Pidsadnyi',
    license='MIT license',
    author_email='oleg.pidsadnyi@gmail.com',
    url='https://github.com/olegpidsadnyi/pytest-bdd',
    version=pytest_bdd.__version__,
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
    cmdclass={'test': Tox},
    install_requires=[
        'pytest>=2.6.0',
        'glob2',
        'Mako',
    ],
    # the following makes a plugin available to py.test
    entry_points={
        'pytest11': [
            'pytest-bdd = pytest_bdd.plugin',
            'pytest-bdd-cucumber-json = pytest_bdd.cucumber_json',
            'pytest-bdd-generation = pytest_bdd.generation',
        ],
        'console_scripts': [
            'pytest-bdd = pytest_bdd.scripts:main'
        ]
    },
    tests_require=['detox'],
    packages=['pytest_bdd'],
    include_package_data=True,
)
