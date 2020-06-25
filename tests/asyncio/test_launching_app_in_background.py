import asyncio
from datetime import datetime, timedelta

import aiohttp

from pytest_bdd import given, when, then, scenarios, parsers

scenarios("test_launching_app_in_background.feature")


@given("i have launched app")
async def i_have_launched_app(launch_dummy_app):
    pass


@when(parsers.parse("i post input variable to have value of {value:d}"))
async def i_post_input_variable(value, dummy_server_host, unused_tcp_port):
    async with aiohttp.ClientSession() as session:
        endpoint = "http://{}:{}/pre-computation-value".format(dummy_server_host, unused_tcp_port)
        await session.put(endpoint, json={"value": value})


@then(parsers.parse("output value should be equal to {expected_value:d}"))
async def output_value_should_be_equal_to(expected_value, dummy_server_host, unused_tcp_port, app_tick_interval):
    async with aiohttp.ClientSession() as session:
        timeout = app_tick_interval * 10
        end_time = datetime.now() + timedelta(seconds=timeout)

        while datetime.now() < end_time:
            url = "http://{}:{}/post-computation-value".format(dummy_server_host, unused_tcp_port)
            response = await session.get(url)
            output_value = int(await response.text())

            if output_value == expected_value:
                break

            await asyncio.sleep(app_tick_interval)
        else:
            raise AssertionError(
                "Output value of {} isn't equal to expected value of {}.".format(output_value, expected_value)
            )
