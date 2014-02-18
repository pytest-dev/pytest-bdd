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

test_argumented_step = scenario('args_steps.feature', 'Test argumented step')


def test_multiple_given(request):
    """Using the same given fixture raises an error."""
    test = scenario(
        'args_steps.feature',
        'Using the same given fixture raises an error',
    )
    with pytest.raises(GivenAlreadyUsed):
        test(request)


@pytest.fixture
def apples_quantity():
    return 2


@pytest.fixture
def apples_color():
    return 'green'


@pytest.fixture
def apples(apples_quantity, apples_color):
    return "{0} {1}".format(apples_quantity, apples_color)


@pytest.fixture
def values():
    return ['1', '2', '1', '0', '999999']


@given(re.compile('I buy (?P<apples_quantity>\d+) (?P<apples_color>\w+) apples'))
def i_buy_apples(apples):
    """I buy apples."""


@given(re.compile(r'I have (?P<euro>\d+) Euro'))
def i_have(euro, values):
    assert euro == values.pop(0)


@given('I have an argument')
def argument():
    """I have an argument."""
    return dict(arg=1)


@when(re.compile(r'I pay (?P<euro>\d+) Euro'))
def i_pay(euro, values, request):
    assert euro == values.pop(0)


@when(re.compile('I get argument (?P<arg>\d+)'))
def get_argument(argument, arg):
    """Getting argument."""
    argument['arg'] = arg


@then(re.compile(r'I should have (?P<euro>\d+) Euro'))
def i_should_have(euro, values):
    assert euro == values.pop(0)


@then(re.compile('My argument should be (?P<arg>\d+)'))
def assert_that_my_argument_is_arg(argument, arg):
    """Assert that arg from when equals arg."""
    assert argument['arg'] == arg


@then(re.compile('I should have (?P<quantity>\d+) (?P<color>\w+) apples'))
def test_i_should_have_apples(apples, quantity, color):

    assert apples == "{0} {1}".format(quantity, color)
