"""Scenario Outline tests."""
import re

import pytest

from pytest_bdd import given, when, then, scenario
from pytest_bdd import exceptions


@scenario(
    'outline.feature',
    'Outlined given, when, thens',
    example_converters=dict(start=int, eat=float, left=str)
)
def test_outlined():
    assert test_outlined.parametrize.args == (
        [u'start', u'eat', u'left'], [[12, 5.0, '7'], [5, 4.0, '1']])


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

    with pytest.raises(exceptions.ScenarioExamplesNotValidError) as exc:
        @scenario(
            'outline.feature',
            'Outlined with wrong examples',
        )
        def wrongly_outlined():
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


@scenario(
    'outline.feature',
    'Outlined given, when, thens',
    example_converters=dict(start=int, eat=float, left=str)
)
def test_outlined_with_other_fixtures(other_fixture):
    """Test outlined scenario also using other parametrized fixture."""


@scenario(
    'outline.feature',
    'Outlined with vertical example table',
    example_converters=dict(start=int, eat=float, left=str)
)
def test_vertical_example():
    """Test outlined scenario with vertical examples table."""
    assert test_vertical_example.parametrize.args == (
        [u'start', u'eat', u'left'], [[12, 5.0, '7'], [2, 1.0, '1']])


def test_empty_example_values():
    """Test outlined scenario with empty example values."""

    @scenario(
        'outline.feature',
        'Outlined with empty example values',
    )
    def test_scenario():
        pass

    assert test_scenario.parametrize.args == (
        [u'start', u'eat', u'left'], [['#', '', '']])

    @scenario(
        'outline.feature',
        'Outlined with empty example values vertical',
    )
    def test_scenario():
        pass

    assert test_scenario.parametrize.args == (
        [u'start', u'eat', u'left'], [['#', '', '']])
