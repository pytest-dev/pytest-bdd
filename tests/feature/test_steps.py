from pytest_bdd import scenario, given, when, then


test_steps = scenario('steps.feature', 'Executed step by step')


@given('I have a foo fixture with value "foo"')
def foo():
    return 'foo'


@given('there is a list')
def results():
    return []


@when('I append 1 to the list')
def append_1(results):
    results.append(1)


@when('I append 2 to the list')
def append_2(results):
    results.append(2)


@when('I append 3 to the list')
def append_3(results):
    results.append(3)


@then('foo should have value "foo"')
def foo_is_foo(foo):
    assert foo == 'foo'


@then('the list should be [1, 2, 3]')
def check_results(results):
    assert results == [1, 2, 3]


test_when_first = scenario('steps.feature', 'When step can be the first')


@when('I do nothing')
def do_nothing():
    pass


@then('I make no mistakes')
def no_errors():
    assert True


test_then_after_given = scenario('steps.feature', 'Then step can follow Given step')


@given('xyz')
def xyz():
    """Used in the test_same_step_name."""
    return

test_conftest = scenario('steps.feature', 'All steps are declared in the conftest')
