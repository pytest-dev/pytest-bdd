"""Test feature background."""

import textwrap


FEATURE = """\
Feature: Background support

    Background:
        Given foo has a value "bar"
        And a background step with multiple lines:
            one
            two


    Scenario: Basic usage
        Then foo should have value "bar"

    Scenario: Background steps are executed first
        Given foo has no value "bar"
        And foo has a value "dummy"

        Then foo should have value "dummy"
        And foo should not have value "bar"
"""

STEPS = r"""\
import re
import pytest
from pytest_bdd import given, then, parsers

@pytest.fixture
def foo():
    return {}


@given(parsers.re(r"a background step with multiple lines:\n(?P<data>.+)", flags=re.DOTALL))
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


@then('foo should have value "bar"')
def foo_has_bar(foo):
    assert foo["bar"] == "bar"


@then('foo should have value "dummy"')
def foo_has_dummy(foo):
    assert foo["dummy"] == "dummy"


@then('foo should not have value "bar"')
def foo_has_no_bar(foo):
    assert "bar" not in foo

"""


def test_background_basic(testdir):
    """Test feature background."""
    testdir.makefile(".feature", background=textwrap.dedent(FEATURE))

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("background.feature", "Basic usage")
        def test_background():
            pass

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_background_check_order(testdir):
    """Test feature background to ensure that backound steps are executed first."""

    testdir.makefile(".feature", background=textwrap.dedent(FEATURE))

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("background.feature", "Background steps are executed first")
        def test_background():
            pass

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
