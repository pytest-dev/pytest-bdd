"""Function name same as step name."""

from pytest_bdd import (
    scenario,
    when,
)


@scenario('same_function_name.feature', 'When function name same as step name')
def test_when_function_name_same_as_step_name():
    pass


@when('something')
def something():
    return 'something'
