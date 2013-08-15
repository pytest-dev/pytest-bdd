"""Test feature base dir."""
import os.path

import pytest

from pytest_bdd import scenario


@pytest.fixture(params=[
    'When step can be the first',
])
def scenario_name(request):
    return request.param


@pytest.fixture
def pytestbdd_feature_base_dir():
    return '/does/not/exist'


def test_feature_path(request, scenario_name):
    """Test feature base dir."""
    sc = scenario('steps.feature', scenario_name)
    exc = pytest.raises(IOError, sc, request)

    assert os.path.join('/does/not/exist/', 'steps.feature') in str(exc.value)
