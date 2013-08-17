import pytest

from pytest_bdd import scenario
from pytest_bdd.scenario import ScenarioNotFound


def test_scenario_not_found(request):
    """Test the situation when scenario is not found."""
    test_not_found = scenario(
        'not_found.feature',
        'NOT FOUND'
    )

    with pytest.raises(ScenarioNotFound):
        test_not_found(request)
