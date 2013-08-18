"""Test wrong feature syntax."""

import pytest

from pytest_bdd import scenario
from pytest_bdd.feature import FeatureError


@pytest.fixture(params=[
    'When after then',
    'Then first',
    'Given after When',
    'Given after Then',
])
def scenario_name(request):
    return request.param


def test_wrong(request, scenario_name):
    """Test wrong feature scenarios."""

    sc = scenario('wrong.feature', scenario_name)
    with pytest.raises(FeatureError):
        sc(request)


def test_verbose_output(request):
    """Test verbose output of failed feature scenario"""
    sc = scenario('wrong.feature', 'When after then')
    with pytest.raises(FeatureError) as excinfo:
        sc(request)

    msg, line_number, line = excinfo.value.args

    assert line_number == 4
    assert line == 'When I do it again'
