# coding: utf-8
"""Tests for testing cases when we have unicode in feature file."""

import sys
import pytest
import functools
from pytest_bdd import (
    given,
    parsers,
    scenario,
    then,
)

scenario = functools.partial(scenario, 'unicode.feature')


@scenario('Кроки в .feature файлі містять юнікод')
def test_steps_in_feature_file_have_unicode():
    pass


@scenario(u'Steps in .py file have unicode')
def test_steps_in_py_file_have_unicode():
    pass


pattern = r"(?P<content>'\w+')"


@pytest.fixture
def string():
    """String fixture."""
    return {'content': ''}


@given(parsers.parse(u"у мене є рядок який містить '{content}'"))
def there_is_a_string_with_content(content, string):
    """Create string with unicode content."""
    string['content'] = content


@given("there is an other string with content 'якийсь контент'")
def there_is_an_other_string_with_content(string):
    """Create other string with unicode content."""
    string['content'] = u"с каким-то контентом"


@then("I should see that the other string equals to content 'якийсь контент'")
def assert_that_the_other_string_equals_to_content(string):
    """Assert that the other string equals to content."""
    assert string['content'] == u"с каким-то контентом"


@then(parsers.parse("I should see that the string equals to content '{content}'"))
def assert_that_the_string_equals_to_content(content, string):
    """Assert that the string equals to content."""
    assert string['content'] == content
    if sys.version_info < (3, 0):
        assert isinstance(content, unicode)
