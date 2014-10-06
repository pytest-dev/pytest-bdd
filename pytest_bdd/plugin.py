"""Pytest plugin entry point. Used for any fixtures needed."""
import os.path
import time

import pytest

from . import (
    given,
    when,
    then,
)


@pytest.fixture
def pytestbdd_feature_base_dir(request):
    """Base feature directory."""
    return os.path.dirname(request.module.__file__)


def pytest_addhooks(pluginmanager):
    """Register plugin hooks."""
    from pytest_bdd import hooks
    pluginmanager.addhooks(hooks)


@pytest.mark.tryfirst
def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Mark step as failed for later reporting.

    Also store step start time.
    """
    step.failed = True
    scenario.failed = True
    if step.start:
        step.stop = time.time()
    for step in scenario.steps[scenario.steps.index(step):]:
        step.failed = True


@pytest.mark.tryfirst
def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    """Store step start time."""
    step.start = time.time()


@pytest.mark.tryfirst
def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    """Store step duration."""
    if step.start and not step.stop:
        step.stop = time.time()


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
                'duration': step.stop - step.start
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


def pytest_addoption(parser):
    """Add pytest-bdd options."""
    parser.getgroup("bdd", "BDD")


@given('trace')
@when('trace')
@then('trace')
def trace():
    """Enter pytest's pdb trace."""
    pytest.set_trace()
