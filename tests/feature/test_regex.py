import re
from pytest_bdd import scenario, given, when, then


test_steps = scenario('regex.feature', 'Executed with steps matching regex step definitons')


@given('I have a foo fixture with value "foo"')
def foo():
    return 'foo'


@given('there is a list')
def results():
    return []


@when(re.compile('I append (?P<n>\d+) to the list'))
def append_to_list(results, n):
    results.append(int(n))


@then('foo should have value "foo"')
def foo_is_foo(foo):
    assert foo == 'foo'


@then('the list should be [1, 2, 3]')
def check_results(results):
    assert results == [1, 2, 3]
