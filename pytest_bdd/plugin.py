"""Pytest plugin entry point. Used for any fixtures needed."""

import pytest

from . import given, when, then
from . import cucumber_json
from . import generation
from . import reporting

from .fixtures import *


def pytest_addhooks(pluginmanager):
    """Register plugin hooks."""
    from pytest_bdd import hooks
    try:
        # pytest >= 2.8
        pluginmanager.add_hookspecs(hooks)
    except AttributeError:
        # pytest < 2.8
        pluginmanager.addhooks(hooks)


@given('trace')
@when('trace')
@then('trace')
def trace():
    """Enter pytest's pdb trace."""
    pytest.set_trace()


def pytest_addoption(parser):
    """Add pytest-bdd options."""
    cucumber_json.add_options(parser)
    generation.add_options(parser)


@pytest.mark.trylast
def pytest_configure(config):
    """Configure all subplugins."""
    cucumber_json.configure(config)


def pytest_unconfigure(config):
    """Unconfigure all subplugins."""
    cucumber_json.unconfigure(config)


@pytest.mark.hookwrapper
def pytest_runtest_makereport(item, call):
    outcome = yield
    reporting.runtest_makereport(item, call, outcome.get_result())


@pytest.mark.tryfirst
def pytest_bdd_before_scenario(request, feature, scenario):
    reporting.before_scenario(request, feature, scenario)


@pytest.mark.tryfirst
def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    reporting.step_error(request, feature, scenario, step, step_func, step_func_args, exception)


@pytest.mark.tryfirst
def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    reporting.before_step(request, feature, scenario, step, step_func)


@pytest.mark.tryfirst
def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    reporting.after_step(request, feature, scenario, step, step_func, step_func_args)


def pytest_cmdline_main(config):
    generation.cmdline_main(config)


def pytest_bdd_apply_tag(tag, function):
    mark = getattr(pytest.mark, tag)
    return mark(function)
