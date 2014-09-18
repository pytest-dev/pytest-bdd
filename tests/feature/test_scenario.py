"""Test scenario decorator."""
import pytest

from pytest_bdd import scenario
from pytest_bdd import exceptions


def test_scenario_not_found(request):
    """Test the situation when scenario is not found."""

    with pytest.raises(exceptions.ScenarioNotFound) as exc_info:
        scenario(
            'not_found.feature',
            'NOT FOUND'
        )
    assert exc_info.value.args[0].startswith('Scenario "NOT FOUND" in feature "[Empty]" in {feature_path}'.format(
        feature_path=request.fspath.join('..', 'not_found.feature')))


def test_scenario_comments(request):
    """Test comments inside scenario."""

    @scenario(
        'comments.feature',
        'Comments'
    )
    def test():
        pass

    test(request)
