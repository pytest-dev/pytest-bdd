"""Test feature background."""
from textwrap import dedent

# language=gherkin
FEATURE = '''\
Feature: Background support

    Background:
        Given foo has a value "bar"
        And a background step with multiple lines:
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

# language=python
STEPS = r"""\
import pytest

from pytest_bdd import given, then, parsers

@pytest.fixture
def foo():
    return {}


@given(parsers.re(r"a background step .*"))
def multi_line(step):
    assert step.doc_string.content == "one\ntwo"


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


def test_background_basic(testdir, tmp_path):
    """Test feature background."""
    (tmp_path / "background.feature").write_text(dedent(FEATURE))

    testdir.makeconftest(STEPS)

    testdir.makepyfile(
        # language=python
        f'''\
        from pathlib import Path

        from pytest_bdd import scenario

        @scenario(Path(r"'''
        f"{tmp_path / 'background.feature'}"
        """"), "Basic usage")
        def test_background():
            pass
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_background_check_order(testdir, tmp_path):
    """Test feature background to ensure that background steps are executed first."""

    (tmp_path / "background.feature").write_text(dedent(FEATURE))

    testdir.makeconftest(STEPS)

    testdir.makepyfile(
        # language=python
        f'''\
        from pathlib import Path

        from pytest_bdd import scenario

        @scenario(Path(r"'''
        f"{tmp_path / 'background.feature'}"
        """"), "Background steps are executed first")
        def test_background():
            pass
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
