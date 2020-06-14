"""Given tests."""
import pytest

from pytest_bdd import given, then, scenario
from pytest_bdd.steps import StepError


@given("I have foo")
def foo():
    return "foo"


given("I have alias for foo", fixture="foo")
given("I have an alias to the root fixture", fixture="root")


@given("I have session foo", scope="session")
def session_foo():
    return "session foo"


@scenario("given.feature", "Test reusing local fixture")
def test_given_with_fixture():
    pass


@scenario("given.feature", "Test reusing root fixture")
def test_root_alias():
    pass


@scenario("given.feature", "Test session given")
def test_session_given():
    pass


@scenario("given.feature", "Test given fixture injection")
def test_given_injection():
    pass


@given("I have injecting given", target_fixture="foo")
def injecting_given():
    return "injected foo"


@then('foo should be "injected foo"')
def foo_is_injected_foo(foo):
    assert foo == "injected foo"


@then('foo should be "foo"')
def foo_is_foo(foo):
    assert foo == "foo"


@then('session foo should be "session foo"')
def session_foo_is_foo(session_foo):
    assert session_foo == "session foo"


@then('root should be "root"')
def root_is_root(root):
    assert root == "root"


def test_decorate_with_fixture():
    """Test given can't be used as decorator when the fixture is specified."""
    with pytest.raises(StepError):

        @given("Foo", fixture="foo")
        def bla():
            pass
