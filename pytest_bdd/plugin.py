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


@pytest.mark.tryfirst
def pytest_runtest_makereport(item, call, __multicall__):
    """Store item in the report object."""
    rep = __multicall__.execute()
    if hasattr(item, 'scenario'):
        rep.item = item
    return rep
