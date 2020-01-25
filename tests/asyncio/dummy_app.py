import asyncio
import contextlib
import time
from contextlib import contextmanager
from multiprocessing.context import Process

import aiohttp
import pytest
import requests
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
        start_time = time.time()
        response = requests.Response()
        response.status_code = HTTP_404_NOT_FOUND

        while response.status_code != HTTP_200_OK and time.time() - start_time <= timeout:
            with contextlib.suppress(requests.exceptions.ConnectionError):
                response = requests.request("POST", f"http://{host}:{port}/health")
            time.sleep(0.01)

        fail_message = f"Timeout expired: failed to start mock REST API in {timeout} seconds"
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

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.stored_value = 0

    async def run(self):
        await asyncio.gather(self.run_getter(), self.run_poster())

    async def run_getter(self):
        async with aiohttp.ClientSession() as session:
            while True:
                await asyncio.sleep(0.1)
                response = await session.get("http://{}:{}/pre-computation-value".format(self.host, self.port))
                self.stored_value = int(await response.text())

    async def run_poster(self):
        async with aiohttp.ClientSession() as session:
            while True:
                await asyncio.sleep(0.1)
                await session.put(
                    "http://{}:{}/post-computation-value".format(self.host, self.port),
                    json={"value": self.stored_value + 1},
                )


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
