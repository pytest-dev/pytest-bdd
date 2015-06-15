"""Test feature background."""
import re

import pytest

from pytest_bdd import (
    given,
    parsers,
    scenario,
    then,
    when,
)


def test_background_basic(request):
    """Test feature background."""
    @scenario(
        "background.feature",
        "Basic usage",
    )
    def test():
        pass

    test(request)


def test_background_check_order(request):
    """Test feature background to ensure that backound steps are executed first."""
    @scenario(
        "background.feature",
        "Background steps are executed first",
    )
    def test():
        pass

    test(request)


@pytest.fixture
def foo():
    return {}


@given(parsers.re(r'a background step with multiple lines:\n(?P<data>.+)', flags=re.DOTALL))
def multi_line(foo, data):
    assert data == "one\ntwo"


@given('foo has a value "bar"')
def bar(foo):
    foo["bar"] = "bar"
    return foo["bar"]


@given('foo has a value "dummy"')
def dummy(foo):
    foo["dummy"] = "dummy"
    return foo["dummy"]


@given('foo has no value "bar"')
def no_bar(foo):
    assert foo["bar"]
    del foo["bar"]


@when('I set foo with a value "foo"')
def set_foo_foo(foo):
    foo["foo"] = "foo"


@then('foo should have value "bar"')
def foo_has_bar(foo):
    assert foo["bar"] == "bar"


@then('foo should have value "foo"')
def foo_has_foo(foo):
    assert foo["foo"] == "foo"


@then('foo should have value "dummy"')
def foo_has_dummy(foo):
    assert foo['dummy'] == "dummy"


@then('foo should not have value "bar"')
def foo_has_no_bar(foo):
    assert "bar" not in foo
