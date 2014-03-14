"""Test step alias when decorated multiple times."""

from pytest_bdd import scenario, given, when, then


@scenario('alias.feature', 'Multiple given alias is not evaluated multiple times')
def test_steps():
    pass


@given('I have an empty list')
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


@then('my list should be [1, 2, 2]')
def check_results(results):
    """Fixtures are not evaluated multiple times, so the list will be [1, 2, 2]"""
    assert results == [1, 2, 2]
