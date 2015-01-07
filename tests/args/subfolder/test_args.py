"""Test step arguments with complex folder structure."""

from pytest_bdd import (
    given,
    parsers,
    scenario,
    then,
    when,
)


@scenario(
    'args.feature',
    'Executed with steps matching step definitons with arguments',
)
def test_steps():
    pass


@given('I have a foo fixture with value "foo"')
def foo():
    return 'foo'


@given('there is a list')
def results():
    return []


@when(parsers.parse('I append {n:d} to the list'))
def append_to_list(results, n):
    results.append(n)


@then('foo should have value "foo"')
def foo_is_foo(foo):
    assert foo == 'foo'


@then('the list should be [1, 2, 3]')
def check_results(results):
    assert results == [1, 2, 3]
