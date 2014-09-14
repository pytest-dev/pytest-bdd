"""Test feature background."""
import pytest

from pytest_bdd import scenario, given, then


def test_background_basic(request):
    """Test feature background."""

    @scenario(
        'background.feature',
        'Basic usage'
    )
    def test():
        pass

    test(request)


def test_background_check_order(request):
    """Test feature background to ensure that backound steps are executed first."""

    @scenario(
        'background.feature',
        'Background steps are executed first'
    )
    def test():
        pass

    test(request)


@pytest.fixture
def foo():
    return {}


@given('foo has a value "bar"')
def bar(foo):
    foo['bar'] = 'bar'
    return foo['bar']


@given('foo has a value "dummy"')
def dummy(foo):
    foo['dummy'] = 'dummy'
    return foo['dummy']


@given('foo has no value "bar"')
def no_bar(foo):
    assert foo['bar']
    del foo['bar']


@then('foo should have value "bar"')
def foo_has_bar(foo):
    assert foo['bar'] == 'bar'


@then('foo should have value "dummy"')
def foo_has_dummy(foo):
    assert foo['dummy'] == 'dummy'


@then('foo should not have value "bar"')
def foo_has_no_bar(foo):
    assert 'bar' not in foo
