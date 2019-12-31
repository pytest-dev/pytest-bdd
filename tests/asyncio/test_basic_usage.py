import asyncio

import aiohttp
import pytest

from pytest_bdd import given, when, then, scenarios, parsers
from tests.asyncio.app import create_server, setup_and_teardown_flask_app, DummyApp

scenarios("basic_usage.feature")


@pytest.fixture
def dummy_server_host():
    return "localhost"


@pytest.fixture
def dummy_server_port():
    return 10000


@pytest.fixture
def launch_dummy_server(dummy_server_host, dummy_server_port):
    with setup_and_teardown_flask_app(create_server(), dummy_server_host, dummy_server_port):
        yield


@pytest.fixture
async def launch_dummy_app(event_loop, launch_dummy_server, dummy_server_host, dummy_server_port):
    app = DummyApp(dummy_server_host, dummy_server_port)
    task = event_loop.create_task(app.run())
    yield
    task.cancel()
    await asyncio.sleep(0)


@given("i have launched app")
async def i_have_launched_app(launch_dummy_app):
    pass


@when(parsers.parse("i post input variable to have value of {value:d}"))
async def i_post_input_variable(value, dummy_server_host, dummy_server_port):
    async with aiohttp.ClientSession() as session:
        endpoint = "http://{}:{}/pre-computation-value".format(dummy_server_host, dummy_server_port)
        await session.put(endpoint, json={"value": value})


@when(parsers.parse("i wait {seconds:d} second(s)"))
async def i_wait(seconds):
    await asyncio.sleep(seconds)


@then(parsers.parse("output value should be equal to {value:d}"))
async def output_value_should_be_equal_to(value, dummy_server_host, dummy_server_port):
    async with aiohttp.ClientSession() as session:
        response = await session.get("http://{}:{}/post-computation-value".format(dummy_server_host, dummy_server_port))
        output_value = int(await response.text())
        assert output_value == value
