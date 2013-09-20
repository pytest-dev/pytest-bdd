"""Test wrong feature syntax."""

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


# @pytest.mark.parametrize(
#     ('feature', 'scenario_name'),
#     [
#         # ('wrong.feature', 'When after then'),
#         # ('wrong.feature', 'Then first'),
#         # ('wrong.feature', 'Given after When'),
#         # ('wrong.feature', 'Given after Then'),
#     ]
# )
# def test_wrong(request, feature, scenario_name):
#     """Test wrong feature scenarios."""

#     sc = scenario(feature, scenario_name)
#     sc(request)
#     with pytest.raises(FeatureError):
#         sc(request)


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
    """Test wrong feature scenarios."""

    sc = scenario('wrong_type_order.feature', scenario_name)
    with pytest.raises(StepTypeError):
        sc(request)


def test_verbose_output(request):
    """Test verbose output of failed feature scenario"""
    sc = scenario('wrong.feature', 'When after then')
    with pytest.raises(FeatureError) as excinfo:
        sc(request)

    msg, line_number, line = excinfo.value.args

    assert line_number == 4
    assert line == 'When I do it again'
