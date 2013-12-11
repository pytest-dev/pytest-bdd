"""Pytest plugin entry point. Used for any fixtures needed."""

import os.path  # pragma: no cover

import pytest  # pragma: no cover


@pytest.fixture  # pragma: no cover
def pytestbdd_feature_base_dir(request):
    """Base feature directory."""
    return os.path.dirname(request.module.__file__)


def pytest_addhooks(pluginmanager):
    """Register plugin hooks."""
    from pytest_bdd import hooks
    pluginmanager.addhooks(hooks)
