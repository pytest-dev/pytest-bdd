import pytest

from pytest_bdd import scenario
from pytest_bdd.scenario import ScenarioNotFound


def test_scenario_not_found(request):
    """Test the situation when scenario is not found."""

    with pytest.raises(ScenarioNotFound):
        scenario(
            'not_found.feature',
            'NOT FOUND'
        )
