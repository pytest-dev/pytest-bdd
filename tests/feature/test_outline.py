"""Scenario Outline tests."""
from pytest_bdd import given, when, then, scenario


test_outlined = scenario(
    'outline.feature',
    'Outlined given, when, thens',
)


@given('there are <start> cucumbers')
def start_cucumbers(start):
    return dict(start=int(start))


@when('I eat <eat> cucumbers')
def eat_cucumbers(start_cucumbers, start, eat):
    start_cucumbers['eat'] = int(eat)


@then('I should have <left> cucumbers')
def should_have_left_cucumbers(start_cucumbers, start, eat, left):
    assert int(start) - int(eat) == int(left)
    assert start_cucumbers['start'] == int(start)
    assert start_cucumbers['eat'] == int(eat)
