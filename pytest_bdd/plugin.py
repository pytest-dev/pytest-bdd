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
    try:
        scenario = item.obj.__scenario__
    except AttributeError:
        pass
    else:
        rep.scenario = {
            'steps': [{
                'name': step._name,
                'type': step.type,
                'line_number': step.line_number
            } for step in scenario.steps],
            'name': scenario.name,
            'line_number': scenario.line_number,
            'feature': {
                'name': scenario.feature.name,
                'filename': scenario.feature.filename,
                'rel_filename': scenario.feature.rel_filename,
                'line_number': scenario.feature.line_number,
                'description': scenario.feature.description
            }
        }
        rep.item = {
            'name': item.name
        }

    return rep
