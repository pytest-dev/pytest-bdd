"""Step arguments tests."""
import functools
import re

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
def _():
    pass


@scenario_when('Argument in when, step 1')
def _():
    pass


@scenario_when('Argument in when, step 2')
def _():
    pass


def test_multiple_given(request):
    """Using the same given fixture raises an error."""
    @scenario_args('Using the same given fixture raises an error')
    def test():
        pass
    with pytest.raises(exceptions.GivenAlreadyUsed):
        test(request)


@given(parsers.re(r'I have (?P<euro>\d+) Euro'), converters=dict(euro=int))
def i_have(euro, values):
    assert euro == values.pop(0)


@when(parsers.re(r'I pay (?P<euro>\d+) Euro'), converters=dict(euro=int))
def _(euro, values, request):
    assert euro == values.pop(0)


@then(parsers.re(r'I should have (?P<euro>\d+) Euro'), converters=dict(euro=int))
def _(euro, values):
    assert euro == values.pop(0)


# test backwards compartibility
@given(re.compile(r'I have an argument (?P<arg>\d+)'))
def argument(arg):
    """I have an argument."""
    return dict(arg=arg)


@when(parsers.re(r'I get argument (?P<arg>\d+)'))
def _(argument, arg):
    """Getting argument."""
    argument['arg'] = arg


@then(parsers.re(r'My argument should be (?P<arg>\d+)'))
def _(argument, arg):
    """Assert that arg from when equals arg."""
    assert argument['arg'] == arg
