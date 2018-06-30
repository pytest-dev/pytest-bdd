"""Scenario Outline tests."""
import re
import textwrap

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
        r"""Scenario \"Outlined with wrong examples\" in the feature \"(.+)\" has not valid examples\. """
        r"""Set of step parameters (.+) should match set of example values """
        r"""(.+)\.""",
        exc.value.args[0]
    )


def test_wrong_vertical_examples_scenario(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    features = testdir.mkdir('features')
    feature = features.join('test.feature')
    feature.write_text(textwrap.dedent(u"""
    Scenario Outline: Outlined with wrong vertical example table
        Given there are <start> cucumbers
        When I eat <eat> cucumbers
        Then I should have <left> cucumbers

        Examples: Vertical
        | start | 12 | 2 |
        | start | 10 | 1 |
        | left  | 7  | 1 |
    """), 'utf-8', ensure=True)
    with pytest.raises(exceptions.FeatureError) as exc:
        @scenario(
            feature.strpath,
            'Outlined with wrong vertical example table',
        )
        def wrongly_outlined():
            pass

    assert exc.value.args[0] == (
        'Scenario has not valid examples. Example rows should contain unique parameters.'
        ' "start" appeared more than once')


def test_wrong_vertical_examples_feature(testdir):
    """Test parametrized feature vertical example table has wrong format."""
    features = testdir.mkdir('features')
    feature = features.join('test.feature')
    feature.write_text(textwrap.dedent(u"""
    Feature: Outlines

        Examples: Vertical
        | start | 12 | 2 |
        | start | 10 | 1 |
        | left  | 7  | 1 |

        Scenario Outline: Outlined with wrong vertical example table
            Given there are <start> cucumbers
            When I eat <eat> cucumbers
            Then I should have <left> cucumbers
    """), 'utf-8', ensure=True)
    with pytest.raises(exceptions.FeatureError) as exc:
        @scenario(
            feature.strpath,
            'Outlined with wrong vertical example table',
        )
        def wrongly_outlined():
            pass

    assert exc.value.args[0] == (
        'Feature has not valid examples. Example rows should contain unique parameters.'
        ' "start" appeared more than once')


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


@given('there are <start> <fruits>')
def start_fruits(start, fruits):
    assert isinstance(start, int)
    return {fruits: dict(start=start)}


@when('I eat <eat> <fruits>')
def eat_fruits(start_fruits, eat, fruits):
    assert isinstance(eat, float)
    start_fruits[fruits]['eat'] = eat


@then('I should have <left> <fruits>')
def should_have_left_fruits(start_fruits, start, eat, left, fruits):
    assert isinstance(left, str)
    assert start - eat == int(left)
    assert start_fruits[fruits]['start'] == start
    assert start_fruits[fruits]['eat'] == eat


@scenario(
    'outline_feature.feature',
    'Outlined given, when, thens',
    example_converters=dict(start=int, eat=float, left=str)
)
def test_outlined_feature():
    assert test_outlined_feature.parametrize.args == (
        ['start', 'eat', 'left'],
        [[12, 5.0, '7'], [5, 4.0, '1']],
        ['fruits'],
        [[u'oranges'], [u'apples']]
    )
