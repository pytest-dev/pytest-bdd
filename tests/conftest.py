from __future__ import annotations

import pytest

pytest_plugins = "pytester"


def pytest_generate_tests(metafunc):
    if "pytest_params" in metafunc.fixturenames:
        parametrizations = [
            pytest.param([], id="no-import-mode"),
            pytest.param(["--import-mode=prepend"], id="--import-mode=prepend"),
            pytest.param(["--import-mode=append"], id="--import-mode=append"),
            pytest.param(["--import-mode=importlib"], id="--import-mode=importlib"),
        ]
        metafunc.parametrize("pytest_params", parametrizations)
