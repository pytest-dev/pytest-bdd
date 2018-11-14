"""Scenario Outline with empty example values tests."""
from pytest_bdd import given, scenario, then, when
from pytest_bdd.utils import get_parametrize_markers_args


@given('there are <start> cucumbers')
def start_cucumbers(start):
    pass


@when('I eat <eat> cucumbers')
def eat_cucumbers(eat):
    pass


@then('I should have <left> cucumbers')
def should_have_left_cucumbers(left):
    pass


@scenario(
    'outline.feature',
    'Outlined with empty example values',
)
def test_scenario_with_empty_example_values(request):
    assert get_parametrize_markers_args(request.node) == (
        [u'start', u'eat', u'left'], [['#', '', '']])


@scenario(
    'outline.feature',
    'Outlined with empty example values vertical',
)
def test_scenario_with_empty_example_values_vertical(request):
    assert get_parametrize_markers_args(request.node) == (
        [u'start', u'eat', u'left'], [['#', '', '']])
