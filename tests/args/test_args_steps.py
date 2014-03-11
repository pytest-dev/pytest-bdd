"""Step arguments tests."""

import functools
import re
import pytest
from pytest_bdd import scenario, given, when, then
from pytest_bdd.scenario import GivenAlreadyUsed


test_steps = scenario(
    'args_steps.feature',
    'Every step takes a parameter with the same name',
)

sc = functools.partial(scenario, 'when_arguments.feature')
test_argument_in_when_step_1 = sc('Argument in when, step 1')
test_argument_in_when_step_2 = sc('Argument in when, step 2')


@pytest.fixture
def values():
    return [1, 2, 1, 0, 999999]


@given(re.compile(r'I have (?P<euro>\d+) Euro'), converters=dict(euro=int))
def i_have(euro, values):
    assert euro == values.pop(0)


@when(re.compile(r'I pay (?P<euro>\d+) Euro'), converters=dict(euro=int))
def i_pay(euro, values, request):
    assert euro == values.pop(0)


@then(re.compile(r'I should have (?P<euro>\d+) Euro'), converters=dict(euro=int))
def i_should_have(euro, values):
    assert euro == values.pop(0)


@given('I have an argument')
def argument():
    """I have an argument."""
    return dict(arg=1)


@when(re.compile('I get argument (?P<arg>\d+)'))
def get_argument(argument, arg):
    """Getting argument."""
    argument['arg'] = arg


@then(re.compile('My argument should be (?P<arg>\d+)'))
def assert_that_my_argument_is_arg(argument, arg):
    """Assert that arg from when equals arg."""
    assert argument['arg'] == arg


def test_multiple_given(request):
    """Using the same given fixture raises an error."""
    test = scenario(
        'args_steps.feature',
        'Using the same given fixture raises an error',
    )
    with pytest.raises(GivenAlreadyUsed):
        test(request)
