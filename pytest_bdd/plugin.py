"""Pytest plugin entry point. Used for any fixtures needed."""
from typing import Collection, Optional, Union
from warnings import warn

import pytest
from _pytest.mark import Mark, MarkDecorator
from _pytest.warning_types import PytestDeprecationWarning

from . import cucumber_json, generation, gherkin_terminal_reporter, given, reporting, steps, then, when
from .steps import Step
from .utils import CONFIG_STACK


def pytest_addhooks(pluginmanager):
    """Register plugin hooks."""
    from pytest_bdd import hooks

    pluginmanager.add_hookspecs(hooks)


@given("trace")
@when("trace")
@then("trace")
def trace():
    """Enter pytest's pdb trace."""
    pytest.set_trace()


@pytest.fixture
def bdd_example():
    """The current scenario outline parametrization.

    If no outline is used, we just return an empty dict to render
    the current template without any actual variable.
    Otherwise pytest_bdd will add all the context variables in this fixture
    from the example definitions in the feature file.
    """
    return {}


@pytest.fixture
def step_registry():
    """Fixture containing registry of all user-defined steps"""


@pytest.fixture
def step_matcher(pytestconfig):
    """Fixture containing matcher to help find step definition for selected step of scenario"""
    return Step.Matcher(pytestconfig)


def pytest_addoption(parser):
    """Add pytest-bdd options."""
    add_bdd_ini(parser)
    steps.add_options(parser)
    cucumber_json.add_options(parser)
    generation.add_options(parser)
    gherkin_terminal_reporter.add_options(parser)


def add_bdd_ini(parser):
    parser.addini("bdd_features_base_dir", "Base features directory.")


@pytest.mark.trylast
def pytest_configure(config):
    """Configure all subplugins."""
    CONFIG_STACK.append(config)
    cucumber_json.configure(config)
    gherkin_terminal_reporter.configure(config)


def pytest_unconfigure(config):
    """Unconfigure all subplugins."""
    CONFIG_STACK.pop()
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
    return generation.cmdline_main(config)


@pytest.hookimpl(hookwrapper=True)
def pytest_bdd_apply_tag(tag, function):
    outcome = yield
    res = outcome.get_result()
    if res is not None:
        warn(
            PytestDeprecationWarning(
                'Will be removed, use instead "pytest_bdd_convert_tag_to_marks". This doesn\'t work with Examples tags'
            )
        )


@pytest.mark.trylast
def pytest_bdd_convert_tag_to_marks(
    feature, scenario, example, tag
) -> Optional[Collection[Union[Mark, MarkDecorator]]]:
    return [getattr(pytest.mark, tag)]


def pytest_bdd_match_step_definition_to_step(request, step) -> "Step.Definition":
    step_registry: Step.Registry = request.getfixturevalue("step_registry")
    step_matcher: Step.Matcher = request.getfixturevalue("step_matcher")

    return step_matcher(step, step_registry)
