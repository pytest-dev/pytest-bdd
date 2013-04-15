"""Test step alias when decorated multiple times."""

from pytest_bdd import scenario, given, when, then


test_steps = scenario('alias.feature', 'Given step alias is an independent copy')


@given('Given I have an empty list')
def results():
    return []


@given('I have foo (which is 1) in my list')
@given('I have bar (alias of foo) in my list')
def foo(results):
    results.append(1)


@when('I do crash (which is 2)')
@when('I do boom (alias of crash)')
def crash(results):
    results.append(2)


@then('my list should be [1, 1, 2, 2]')
def check_results(results):
    """Fixture alias is a copy, so the list will be [1, 1, 2, 2]"""
    assert results == [1, 1, 2, 2]
