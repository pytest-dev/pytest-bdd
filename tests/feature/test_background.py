"""Test feature background."""

from __future__ import annotations

import textwrap

FEATURE = '''\
Feature: Background support

    Background:
        Given foo has a value "bar"
        And a background step with docstring:
        """
            one
            two
        """


    Scenario: Basic usage
        Then foo should have value "bar"

    Scenario: Background steps are executed first
        Given foo has no value "bar"
        And foo has a value "dummy"

        Then foo should have value "dummy"
        And foo should not have value "bar"
'''

STEPS = r"""\
import re
import pytest
from pytest_bdd import given, then, parsers

@pytest.fixture
def foo():
    return {}


@given("a background step with docstring:")
def _(foo, docstring):
    assert docstring == "one\ntwo"


@given('foo has a value "bar"')
def _(foo):
    foo["bar"] = "bar"
    return foo["bar"]


@given('foo has a value "dummy"')
def _(foo):
    foo["dummy"] = "dummy"
    return foo["dummy"]


@given('foo has no value "bar"')
def _(foo):
    assert foo["bar"]
    del foo["bar"]


@then('foo should have value "bar"')
def _(foo):
    assert foo["bar"] == "bar"


@then('foo should have value "dummy"')
def _(foo):
    assert foo["dummy"] == "dummy"


@then('foo should not have value "bar"')
def _(foo):
    assert "bar" not in foo

"""


def test_background_basic(pytester):
    """Test feature background."""
    pytester.makefile(".feature", background=textwrap.dedent(FEATURE))

    pytester.makeconftest(textwrap.dedent(STEPS))

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("background.feature", "Basic usage")
        def test_background():
            pass

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_background_check_order(pytester):
    """Test feature background to ensure that background steps are executed first."""

    pytester.makefile(".feature", background=textwrap.dedent(FEATURE))

    pytester.makeconftest(textwrap.dedent(STEPS))

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("background.feature", "Background steps are executed first")
        def test_background():
            pass

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
