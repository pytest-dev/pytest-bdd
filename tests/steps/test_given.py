import pytest

from pytest_bdd import given, then, scenario
from pytest_bdd.steps import StepError


@given('I have foo')
def foo():
    return 'foo'


@given('I have bar')
def bar():
    return 'bar'


given('I have alias for foo', fixture='foo')
given('I have an alias to the root fixture', fixture='root')
given('I have a given with list of foo and bar fixtures', fixture=['foo', 'bar'])

test_given_with_fixture = scenario('given.feature', 'Test reusing local fixture')

test_root_alias = scenario('given.feature', 'Test reusing root fixture')

test_list_of_fixtures = scenario('given.feature', 'Test of using list of fixtures with given')


@then('foo should be "foo"')
def foo_is_foo(foo):
    assert foo == 'foo'


@then('bar should be "bar"')
def bar_is_bar(bar):
    assert bar == 'bar'


@then('root should be "root"')
def root_is_root(root):
    assert root == 'root'


def test_decorate_with_fixture():
    """Test given can't be used as decorator when the fixture is specified."""

    with pytest.raises(StepError):
        @given('Foo', fixture='foo')
        def bla():
            pass
