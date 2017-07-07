"""Test no strict gherkin for sections."""

import py
import pytest

from pytest_bdd import (
    when,
    scenario,
)


@pytest.fixture
def pytestbdd_strict_gherkin():
    return False


def test_background_no_strict_gherkin(request):
    """Test background no strict gherkin."""
    @scenario(
        "no_sctrict_gherkin_background.feature",
        "Test background",
    )
    def test():
        pass

    test(request)


def test_scenario_no_strict_gherkin(request):
    """Test scenario no strict gherkin."""
    @scenario(
        "no_sctrict_gherkin_scenario.feature",
        "Test scenario",
    )
    def test():
        pass

    test(request)


@pytest.fixture
def foo():
    return {}


@when('foo has a value "bar"')
def bar(foo):
    foo["bar"] = "bar"
    return foo["bar"]


@when('foo is not boolean')
def not_boolean(foo):
    assert foo is not bool


@when('foo has not a value "baz"')
def has_not_baz(foo):
    assert "baz" not in foo
