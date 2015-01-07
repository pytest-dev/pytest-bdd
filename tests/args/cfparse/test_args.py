"""Step arguments tests."""

import functools
from pytest_bdd import (
    given,
    parsers,
    scenario,
    then,
    when,
)

import pytest

from pytest_bdd import exceptions

scenario_when = functools.partial(scenario, '../when_arguments.feature')

scenario_args = functools.partial(scenario, '../args_steps.feature')


@scenario_args('Every step takes a parameter with the same name')
def test_steps():
    pass


@scenario_when('Argument in when, step 1')
def test_argument_in_when_step_1():
    pass


@scenario_when('Argument in when, step 2')
def test_argument_in_when_step_2():
    pass


def test_multiple_given(request):
    """Using the same given fixture raises an error."""
    @scenario_args('Using the same given fixture raises an error')
    def test():
        pass
    with pytest.raises(exceptions.GivenAlreadyUsed):
        test(request)


@given(parsers.cfparse('I have {euro:d} Euro'))
def i_have(euro, values):
    assert euro == values.pop(0)


@when(parsers.cfparse('I pay {euro:d} Euro'))
def i_pay(euro, values, request):
    assert euro == values.pop(0)


@then(parsers.cfparse('I should have {euro:d} Euro'))
def i_should_have(euro, values):
    assert euro == values.pop(0)


@given(parsers.cfparse('I have an argument {arg:Number}', extra_types=dict(Number=int)))
def argument(arg):
    """I have an argument."""
    return dict(arg=arg)


@when(parsers.cfparse('I get argument {arg:d}'))
def get_argument(argument, arg):
    """Getting argument."""
    argument['arg'] = arg


@then(parsers.cfparse('My argument should be {arg:d}'))
def assert_that_my_argument_is_arg(argument, arg):
    """Assert that arg from when equals arg."""
    assert argument['arg'] == arg
