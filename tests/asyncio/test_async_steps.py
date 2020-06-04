import pytest

from pytest_bdd import then, when, given, scenario


@pytest.fixture
def test_value():
    return {"value": 0}


@scenario("test_async_steps.feature", "Async steps are actually executed")
def test_async_steps_do_work(test_value):
    assert test_value["value"] == 3


@scenario("test_async_steps.feature", "Async steps are executed along with regular steps")
def test_async_steps_work_with_regular_ones(test_value):
    assert test_value["value"] == 6


@given("i have async step")
async def async_step(test_value):
    test_value["value"] += 1


@given("i have regular step")
def i_have_regular_step(test_value):
    test_value["value"] += 1


@when("i do async step")
async def i_do_async_step(test_value):
    test_value["value"] += 1


@when("i do regular step")
def i_do_regular_step(test_value):
    test_value["value"] += 1


@then("i should have async step")
async def i_should_have_async_step(test_value):
    test_value["value"] += 1


@then("i should have regular step")
def i_should_have_regular_step(test_value):
    test_value["value"] += 1
