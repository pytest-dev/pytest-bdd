import re
import pytest

from pytest_bdd import given, then, scenario
from pytest_bdd.steps import StepError


@given('I have foo')
def foo():
    return 'foo'

given('I have alias for foo', fixture='foo')
given('I have an alias to the root fixture', fixture='root')

test_given_with_fixture = scenario('given.feature', 'Test reusing local fixture')

test_root_alias = scenario('given.feature', 'Test reusing root fixture')

test_argumented_step = scenario('given.feature', 'Test argumented step')


@then('foo should be "foo"')
def foo_is_foo(foo):
    assert foo == 'foo'


@then('root should be "root"')
def root_is_root(root):
    assert root == 'root'


# def test_decorate_with_fixture():
#     """Test given can't be used as decorator when the fixture is specified."""

#     with pytest.raises(StepError):
#         @given('Foo', fixture='foo')
#         def bla():
#             pass


@pytest.fixture
def apples_quantity():
    return 2


@pytest.fixture
def apples_color():
    return 'green'


@pytest.fixture
def apples(apples_quantity, apples_color):
    return "{0} {1}".format(apples_quantity, apples_color)


@given(re.compile('I buy (?P<apples_quantity>\d+) (?P<apples_color>\w+) apples'))
def i_buy_apples(apples):
    """I buy apples."""


@then(re.compile('I should have (?P<quantity>\d+) (?P<color>\w+) apples'))
def test_i_should_have_apples(apples, quantity, color):

    assert apples == "{0} {1}".format(quantity, color)
