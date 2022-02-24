import pytest

from tests.utils import PYTEST_6

pytest_plugins = "pytester"


def pytest_generate_tests(metafunc):
    if "pytest_params" in metafunc.fixturenames:
        if PYTEST_6:
            parametrizations = [
                pytest.param([], id="no-import-mode"),
                pytest.param(["--import-mode=prepend"], id="--import-mode=prepend"),
                pytest.param(["--import-mode=append"], id="--import-mode=append"),
                pytest.param(["--import-mode=importlib"], id="--import-mode=importlib"),
            ]
        else:
            parametrizations = [[]]
        metafunc.parametrize(
            "pytest_params",
            parametrizations,
        )


# TODO: Remove these before merge
# def pytest_collection_finish(session):
#     """Handle the pytest collection finish hook: configure pyannotate.
#     Explicitly delay importing `collect_types` until all tests have
#     been collected.  This gives gevent a chance to monkey patch the
#     world before importing pyannotate.
#     """
#     from pyannotate_runtime import collect_types
#
#     collect_types.init_types_collection()
#
#
# @pytest.fixture(autouse=True)
# def collect_types_fixture() -> Iterator:
#     from pyannotate_runtime import collect_types
#
#     collect_types.start()
#     yield
#     collect_types.stop()
#
#
# def pytest_sessionfinish(session, exitstatus):
#     from pyannotate_runtime import collect_types
#
#     collect_types.dump_stats("type_info.json")
