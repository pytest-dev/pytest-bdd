"""Test wrong feature syntax."""
import os.path
import re

import pytest

from pytest_bdd import scenario, given, when, then
from pytest_bdd.feature import FeatureError
from pytest_bdd import exceptions


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

    with pytest.raises(FeatureError):
        @scenario(feature, scenario_name)
        def test_scenario():
            pass
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
    @scenario('wrong_type_order.feature', scenario_name)
    def test_wrong_type_order(request):
        pass

    with pytest.raises(exceptions.StepTypeError) as excinfo:
        test_wrong_type_order(request)
    assert re.match(r'Wrong step type \"(\w+)\" while \"(\w+)\" is expected\.', excinfo.value.args[0])


def test_verbose_output(request):
    """Test verbose output of failed feature scenario"""
    with pytest.raises(FeatureError) as excinfo:
        scenario('when_after_then.feature', 'When after then')

    msg, line_number, line, file = excinfo.value.args

    assert line_number == 5
    assert line == 'When I do it again'
    assert file == os.path.join(os.path.dirname(__file__), 'when_after_then.feature')
