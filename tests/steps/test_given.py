import pytest

from pytest_bdd import given, then, scenario
from pytest_bdd.steps import StepError


@given('I have foo')
def foo():
    return 'foo'

given('I have alias for foo', fixture='foo')


test_given_with_fixture = scenario('given.feature', 'Test reusing local fixture')

test_root_alias = scenario('given.feature', 'Test reusing root fixture')

given('I have an alias to the root fixture', fixture='root')


@then('foo should be "foo"')
def foo_is_foo(foo):
    assert foo == 'foo'


@then('root should be "root"')
def root_is_root(root):
    assert root == 'root'


def test_decorate_with_fixture():
    """Test given can't be used as decorator when the fixture is specified."""

    with pytest.raises(StepError):
        @given('Foo', fixture='foo')
        def bla():
            pass
