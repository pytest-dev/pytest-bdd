import pytest

from pytest_bdd.steps import when

from pytest_bdd import given, then, scenario

test_reuse = scenario(
    'parametrized.feature',
    'Parametrized given, when, thens',
    params=['start', 'eat', 'left']
)

test_reuse = pytest.mark.parametrize(['start', 'eat', 'left'], [(12, 5, 7)])(test_reuse)


@given('there are <start> cucumbers')
def start_cucumbers(start):
    return dict(start=start)


@when('I eat <eat> cucumbers')
def eat_cucumbers(start_cucumbers, start, eat):
    assert start_cucumbers['start'] == start


@then('I should have <left> cucumbers')
def should_have_left_cucumbers(start, eat, left):
    assert start - eat == left
