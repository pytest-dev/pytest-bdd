"""Pytest plugin entry point. Used for any fixtures needed."""

import os.path  # pragma: no cover

import pytest  # pragma: no cover

from pytest_bdd import (
    given,
    when,
    then,
)


@pytest.fixture  # pragma: no cover
def pytestbdd_feature_base_dir(request):
    """Base feature directory."""
    return os.path.dirname(request.module.__file__)


def pytest_addhooks(pluginmanager):
    """Register plugin hooks."""
    from pytest_bdd import hooks
    pluginmanager.addhooks(hooks)


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Mark step as failed for later reporting."""
    step.failed = True


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
                'name': step.name,
                'type': step.type,
                'keyword': step.keyword,
                'line_number': step.line_number,
                'failed': step.failed,
            } for step in scenario.steps],
            'name': scenario.name,
            'line_number': scenario.line_number,
            'tags': sorted(scenario.tags),
            'feature': {
                'name': scenario.feature.name,
                'filename': scenario.feature.filename,
                'rel_filename': scenario.feature.rel_filename,
                'line_number': scenario.feature.line_number,
                'description': scenario.feature.description,
                'tags': sorted(scenario.feature.tags),
            }
        }
        rep.item = {
            'name': item.name
        }

    return rep


@given('trace')
@when('trace')
@then('trace')
def trace():
    """Enter pytest's pdb trace."""
    pytest.set_trace()
