"""Test wrong feature syntax."""
import functools
import re

import pytest

from pytest_bdd import scenario, given, when, then
from pytest_bdd.feature import FeatureError
from pytest_bdd.scenario import StepTypeError


@given('something')
def given_something():
    pass


@when('something else')
def when_something_else():
    pass


@then('nevermind')
def then_nevermind():
    pass


@pytest.mark.parametrize(
    ('feature', 'scenario_name'),
    [
        ('when_after_then.feature', 'When after then'),
        ('then_first.feature', 'Then first'),
        ('given_after_when.feature', 'Given after When'),
        ('given_after_then.feature', 'Given after Then'),
    ]
)
def test_wrong(request, feature, scenario_name):
    """Test wrong feature scenarios."""

    sc = scenario(feature, scenario_name)
    with pytest.raises(FeatureError):
        sc(request)
    # TODO: assert the exception args from parameters


@pytest.mark.parametrize(
    'scenario_name',
    [
        'When in Given',
        'When in Then',
        'Then in Given',
        'Given in When',
        'Given in Then',
        'Then in When',
    ]
)
def test_wrong_type_order(request, scenario_name):
    """Test wrong step type order."""
    sc = scenario('wrong_type_order.feature', scenario_name)
    with pytest.raises(StepTypeError) as excinfo:
        sc(request)
    excinfo  # TODO: assert the exception args from parameters


def test_verbose_output(request):
    """Test verbose output of failed feature scenario"""
    sc = scenario('when_after_then.feature', 'When after then')
    with pytest.raises(FeatureError) as excinfo:
        sc(request)

    msg, line_number, line = excinfo.value.args

    assert line_number == 4
    assert line == 'When I do it again'


sc = functools.partial(scenario, 'failing_arguments.feature')
test_argument_in_when_step_1 = sc('Argument in when, step 1')
test_argument_in_when_step_2 = sc('Argument in when, step 2')


@pytest.fixture
@when(re.compile('I get argument (?P<arg>\d+)'))
def get_argument(arg):
    """Getting argument."""
    return dict(arg=arg)


@then(re.compile('My argument should be (?P<arg>\d+)'))
def assert_that_my_argument_is_arg(get_argument, arg):
    """Assert that arg from when equals arg."""
    assert get_argument['arg'] == arg