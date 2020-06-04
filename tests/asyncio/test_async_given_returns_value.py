import pytest

from pytest_bdd import given, parsers, then, scenarios

scenarios("test_async_given_returns_value.feature")


@pytest.fixture
def my_value():
    return 0


@given(parsers.parse("i have given that shadows fixture with value of {value:d}"), target_fixture="my_value")
async def i_have_given_that_shadows_fixture_with_value_of(value):
    return value


@given(parsers.parse("i have given that is a fixture with value of {value:d}"))
async def i_have_given_that_is_a_fixture_with_value_of(value):
    return value


@then(parsers.parse("shadowed fixture value should be equal to {value:d}"))
async def my_fixture_value_should_be_equal_to(value, my_value):
    assert value == my_value


@then(parsers.parse("value of given as a fixture should be equal to {value:d}"))
async def value_of_given_as_a_fixture_should_be_equal_to(value, i_have_given_that_is_a_fixture_with_value_of):
    assert value == i_have_given_that_is_a_fixture_with_value_of
