"""Scenario Outline tests."""
import re

import pytest

from pytest_bdd import given, when, then, scenario
from pytest_bdd import mark
from pytest_bdd.scenario import ScenarioExamplesNotValidError


test_outlined = scenario(
    'outline.feature',
    'Outlined given, when, thens',
    example_converters=dict(start=int, eat=float, left=str)
)


@given('there are <start> cucumbers')
def start_cucumbers(start):
    assert isinstance(start, int)
    return dict(start=start)


@when('I eat <eat> cucumbers')
def eat_cucumbers(start_cucumbers, eat):
    assert isinstance(eat, float)
    start_cucumbers['eat'] = eat


@then('I should have <left> cucumbers')
def should_have_left_cucumbers(start_cucumbers, start, eat, left):
    assert isinstance(left, str)
    assert start - eat == int(left)
    assert start_cucumbers['start'] == start
    assert start_cucumbers['eat'] == eat


def test_wrongly_outlined(request):
    """Test parametrized scenario when the test function lacks parameters."""

    with pytest.raises(ScenarioExamplesNotValidError) as exc:
        @mark.scenario(
            'outline.feature',
            'Outlined with wrong examples',
        )
        def wrongly_outlined(request):
            pass

    assert re.match(
        """Scenario \"Outlined with wrong examples\" in the feature \"(.+)\" has not valid examples\. """
        """Set of step parameters (.+) should match set of example values """
        """(.+)\.""",
        exc.value.args[0]
    )


@pytest.fixture(params=[1, 2, 3])
def other_fixture(request):
    return request.param


@mark.scenario(
    'outline.feature',
    'Outlined given, when, thens',
    example_converters=dict(start=int, eat=float, left=str)
)
def test_outlined_with_other_fixtures(other_fixture):
    """Test outlined scenario also using other parametrized fixture."""
