import asyncio
import contextlib
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from multiprocessing.context import Process

import aiohttp
import pytest
import requests
from async_generator import yield_, async_generator
from flask import Flask, jsonify
from flask import request
from flask_api.status import HTTP_404_NOT_FOUND, HTTP_200_OK


@contextmanager
def setup_and_teardown_flask_app(app: Flask, host: str, port: int):
    """
    Manages setup of provided flask app on given `host` and `port` and its teardown.

    As for setup process following things are done:
        * `/health` endpoint is added to provided flask app,
        * app is launched in separate process,
        * function waits for flask app to fully launch - to do this it repetitively checks `/health` endpoint if it will
            return status code 200.

    Example use of this function in fixture:

    >>> with setup_and_teardown_flask_app(Flask(__name__), "localhost", 10000):
    >>>     yield

    :param app: app to launch
    :param host: host on which to launch app
    :param port: port on which to launch app
    """

    def wait_for_flask_app_to_be_accessible():
        timeout = 1
        end_time = datetime.now() + timedelta(seconds=timeout)
        response = requests.Response()
        response.status_code = HTTP_404_NOT_FOUND

        while response.status_code != HTTP_200_OK and datetime.now() < end_time:
            with contextlib.suppress(requests.exceptions.ConnectionError):
                response = requests.request("POST", "http://{}:{}/health".format(host, port))
            time.sleep(0.01)

        fail_message = "Timeout expired: failed to start mock REST API in {} seconds".format(timeout)
        assert response.status_code == HTTP_200_OK, fail_message

    app.route("/health", methods=["POST"])(lambda: "OK")

    process = Process(target=app.run, args=(host, port))
    process.start()

    wait_for_flask_app_to_be_accessible()
    yield

    process.terminate()
    process.join()


def create_server():
    app = Flask(__name__)
    app.pre_computation_value = 0
    app.post_computation_value = 0

    @app.route("/pre-computation-value", methods=["PUT"])
    def set_pre_computation_value():
        app.pre_computation_value = request.json["value"]
        return ""

    @app.route("/pre-computation-value", methods=["GET"])
    def get_pre_computation_value():
        return jsonify(app.pre_computation_value)

    @app.route("/post-computation-value", methods=["PUT"])
    def set_post_computation_value():
        app.post_computation_value = request.json["value"]
        return ""

    @app.route("/post-computation-value", methods=["GET"])
    def get_post_computation_value():
        return jsonify(app.post_computation_value)

    return app


class DummyApp:
    """
    This has to simulate real application that gets input from server, processes it and posts it.
    """

    def __init__(self, host, port, tick_rate_s):
        self.host = host
        self.port = port
        self.tick_rate_s = tick_rate_s
        self.stored_value = 0

    async def run(self):
        await asyncio.gather(self.run_getter(), self.run_poster())

    async def run_getter(self):
        async with aiohttp.ClientSession() as session:
            while True:
                response = await session.get("http://{}:{}/pre-computation-value".format(self.host, self.port))
                self.stored_value = int(await response.text())
                await asyncio.sleep(self.tick_rate_s)

    async def run_poster(self):
        async with aiohttp.ClientSession() as session:
            while True:
                await session.put(
                    "http://{}:{}/post-computation-value".format(self.host, self.port),
                    json={"value": self.stored_value + 1},
                )
                await asyncio.sleep(self.tick_rate_s)


@pytest.fixture
def dummy_server_host():
    return "localhost"


@pytest.fixture
def launch_dummy_server(dummy_server_host, unused_tcp_port):
    with setup_and_teardown_flask_app(create_server(), dummy_server_host, unused_tcp_port):
        yield


@pytest.fixture
def app_tick_interval():
    return 0.01


@pytest.fixture
@async_generator
async def launch_dummy_app(event_loop, launch_dummy_server, dummy_server_host, unused_tcp_port, app_tick_interval):
    app = DummyApp(dummy_server_host, unused_tcp_port, app_tick_interval)
    task = event_loop.create_task(app.run())
    await yield_(None)
    task.cancel()
    await asyncio.sleep(0)
