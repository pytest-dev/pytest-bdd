"""Function name same as step name."""

from pytest_bdd import scenario, when

from . import feature

from . import types


@scenario("function.feature", "With function prefix_by_type")
def test_when_function_is_called():
    pass


@when("is called")
def something():
    assert feature.prefix_by_type(types.FEATURE) == """Feature"""

