#!/usr/bin/env python
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
    author='Oleg Pidsadnyi',
    author_email='oleg.podsadny@gmail.com',
    version='0.2',
    cmdclass={'test': PyTest},
    install_requires=[
        'pytest',
    ],
    tests_require=['mock'],
    packages=['pytest_bdd'],
)
