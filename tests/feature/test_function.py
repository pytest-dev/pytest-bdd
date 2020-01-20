"""Function name same as step name."""

from pytest_bdd import scenario, when

from pytest_bdd import feature

from pytest_bdd import types


@scenario("function.feature", "With function prefix_by_type")
def test_when_function_is_called():
    pass


@when("is called")
def is_called():
    assert feature.prefix_by_type(types.FEATURE) == """Feature: """
    assert feature.prefix_by_type("NA") == """<N/A type> NA"""
