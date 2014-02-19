#!/usr/bin/env python
import os
import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


version = '0.6.10'


class Tox(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = ['--recreate']
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import detox.main
        errno = detox.main.main(self.test_args)
        sys.exit(errno)


dirname = os.path.dirname(__file__)

long_description = (
    open(os.path.join(dirname, 'README.rst')).read() + '\n' +
    open(os.path.join(dirname, 'CHANGES.rst')).read()
)

setup(
    name='pytest-bdd',
    description='BDD for pytest',
    long_description=long_description,
    author='Oleg Pidsadnyi',
    license='MIT license',
    author_email='oleg.podsadny@gmail.com',
    url='https://github.com/olegpidsadnyi/pytest-bdd',
    version=version,
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
        'pytest',
    ],
    # the following makes a plugin available to py.test
    entry_points={
        'pytest11': [
            'pytest-bdd = pytest_bdd.plugin',
        ]
    },
    tests_require=['detox'],
    packages=['pytest_bdd'],
)
