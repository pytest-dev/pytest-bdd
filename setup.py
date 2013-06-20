#!/usr/bin/env python
"""
PyTest-BDD
==========

Implements a subset of Gherkin language for the behavior-driven development and
automated testing. Benefits from the pytest and its dependency injection pattern
for the true just enough specifications and maximal reusability of the BDD
definitions.

Example
```````

publish_article.feature:

.. code:: gherkin

    Scenario: Publishing the article
        Given I'm an author user
        And I have an article
        When I go to the article page
        And I press the publish button
        Then I should not see the error message
        And the article should be published  # Note: will query the database


test_publish_article.py:

.. code:: python

    from pytest_bdd import scenario, given, when, then

    test_publish = scenario('publish_article.feature', 'Publishing the article')


    @given('I have an article')
    def article(author):
        return create_test_article(author=author)


    @when('I go to the article page')
    def go_to_article(article, browser):
        browser.visit(urljoin(browser.url, '/manage/articles/{0}/'.format(article.id)))


    @when('I press the publish button')
    def publish_article(browser):
        browser.find_by_css('button[name=publish]').first.click()


    @then('I should not see the error message')
    def no_error_message(browser):
        with pytest.raises(ElementDoesNotExist):
            browser.find_by_css('.message.error').first


    @then('And the article should be published')
    def article_is_published(article):
        article.refresh()  # Refresh the object in the SQLAlchemy session
        assert article.is_published

Installation
````````````

.. code:: bash

    $ pip install pytest-bdd

Links
`````

* `website <https://github.com/olegpidsadnyi/pytest-bdd>`_
* `documentation <https://pytest-bdd.readthedocs.org/en/latest/>`_

"""
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
    long_description=__doc__,
    author='Oleg Pidsadnyi',
    license='MIT license',
    author_email='oleg.podsadny@gmail.com',
    url='https://github.com/olegpidsadnyi/pytest-bdd',
    version='0.4.6',
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
