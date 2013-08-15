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
    pytest.raises(FeatureError, sc, request)
