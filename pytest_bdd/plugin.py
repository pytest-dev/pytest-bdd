"""Pytest plugin entry point. Used for any fixtures needed."""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable, cast

import pytest

from . import cucumber_json, generation, gherkin_terminal_reporter, given, reporting, then, when
from .utils import CONFIG_STACK

if TYPE_CHECKING:
    from typing import Any, Generator

    from _pytest.config import Config, PytestPluginManager
    from _pytest.config.argparsing import Parser
    from _pytest.fixtures import FixtureRequest
    from _pytest.nodes import Item
    from _pytest.runner import CallInfo
    from pluggy._result import _Result

    from .parser import Feature, Scenario, Step


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    from pytest_bdd import hooks

    pluginmanager.add_hookspecs(hooks)


@given("trace")
@when("trace")
@then("trace")
def _() -> None:
    """Enter pytest's pdb trace."""
    pytest.set_trace()


@pytest.fixture
def _pytest_bdd_example() -> dict:
    """The current scenario outline parametrization.

    This is used internally by pytest_bdd.

    If no outline is used, we just return an empty dict to render
    the current template without any actual variable.
    Otherwise pytest_bdd will add all the context variables in this fixture
    from the example definitions in the feature file.
    """
    return {}


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    add_bdd_ini(parser)
    cucumber_json.add_options(parser)
    generation.add_options(parser)
    gherkin_terminal_reporter.add_options(parser)


def add_bdd_ini(parser: Parser) -> None:
    parser.addini("bdd_features_base_dir", "Base features directory.")


@pytest.hookimpl(trylast=True)
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    CONFIG_STACK.append(config)
    cucumber_json.configure(config)
    gherkin_terminal_reporter.configure(config)


def pytest_unconfigure(config: Config) -> None:
    """Unconfigure all subplugins."""
    CONFIG_STACK.pop()
    cucumber_json.unconfigure(config)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Item, call: CallInfo) -> Generator[None, _Result, None]:
    outcome = yield
    reporting.runtest_makereport(item, call, outcome.get_result())


@pytest.hookimpl(tryfirst=True)
def pytest_bdd_before_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario) -> None:
    reporting.before_scenario(request, feature, scenario)


@pytest.hookimpl(tryfirst=True)
def pytest_bdd_step_error(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable,
    step_func_args: dict,
    exception: Exception,
) -> None:
    reporting.step_error(request, feature, scenario, step, step_func, step_func_args, exception)


@pytest.hookimpl(tryfirst=True)
def pytest_bdd_before_step(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, step_func: Callable
) -> None:
    reporting.before_step(request, feature, scenario, step, step_func)


@pytest.hookimpl(tryfirst=True)
def pytest_bdd_after_step(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable,
    step_func_args: dict[str, Any],
) -> None:
    reporting.after_step(request, feature, scenario, step, step_func, step_func_args)


def pytest_cmdline_main(config: Config) -> int | None:
    return generation.cmdline_main(config)


def pytest_bdd_apply_tag(tag: str, function: Callable) -> Callable:
    mark = getattr(pytest.mark, tag)
    marked = mark(function)
    return cast(Callable, marked)
