import asyncio

import aiohttp

from pytest_bdd import given, when, then, scenarios, parsers

scenarios("launching_app_in_background.feature")


@given("i have launched app")
async def i_have_launched_app(launch_dummy_app):
    pass


@when(parsers.parse("i post input variable to have value of {value:d}"))
async def i_post_input_variable(value, dummy_server_host, unused_tcp_port):
    async with aiohttp.ClientSession() as session:
        endpoint = "http://{}:{}/pre-computation-value".format(dummy_server_host, unused_tcp_port)
        await session.put(endpoint, json={"value": value})


# TODO: instead of waiting here, add loop to "then" step to request GET every 0.1s
@when(parsers.parse("i wait {seconds:d} second(s)"))
async def i_wait(seconds):
    await asyncio.sleep(seconds)


@then(parsers.parse("output value should be equal to {value:d}"))
async def output_value_should_be_equal_to(value, dummy_server_host, unused_tcp_port):
    async with aiohttp.ClientSession() as session:
        response = await session.get("http://{}:{}/post-computation-value".format(dummy_server_host, unused_tcp_port))
        output_value = int(await response.text())
        assert output_value == value
