"""Pytest plugin entry point. Used for any fixtures needed."""
from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

import pytest
from _pytest.mark import Mark, MarkDecorator
from _pytest.python import Metafunc

from . import cucumber_json, generation, gherkin_terminal_reporter, given, steps, then, when
from .reporting import ScenarioReporterPlugin
from .runner import ScenarioRunner
from .steps import StepHandler
from .utils import CONFIG_STACK

if TYPE_CHECKING:  # pragma: no cover
    from typing import Collection

    from _pytest.config import Config, PytestPluginManager
    from _pytest.config.argparsing import Parser


def pytest_addhooks(pluginmanager: PytestPluginManager) -> None:
    """Register plugin hooks."""
    from pytest_bdd import hooks

    pluginmanager.add_hookspecs(hooks)


@given("trace")
@when("trace")
@then("trace")
def trace() -> None:
    """Enter pytest's pdb trace."""
    pytest.set_trace()


@pytest.fixture
def step_registry() -> StepHandler.Registry:
    """Fixture containing registry of all user-defined steps"""


@pytest.fixture
def step_matcher(pytestconfig) -> StepHandler.Matcher:
    """Fixture containing matcher to help find step definition for selected step of scenario"""
    return StepHandler.Matcher(pytestconfig)  # type: ignore[call-arg]


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    add_bdd_ini(parser)
    steps.add_options(parser)
    cucumber_json.add_options(parser)
    generation.add_options(parser)
    gherkin_terminal_reporter.add_options(parser)


def add_bdd_ini(parser: Parser) -> None:
    parser.addini("bdd_features_base_dir", "Base features directory.")


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    config.addinivalue_line("markers", "pytest_bdd_scenario: marker to identify pytest_bdd tests")
    CONFIG_STACK.append(config)
    cucumber_json.configure(config)
    gherkin_terminal_reporter.configure(config)
    config.pluginmanager.register(ScenarioReporterPlugin())
    config.pluginmanager.register(ScenarioRunner())


def pytest_unconfigure(config: Config) -> None:
    """Unconfigure all subplugins."""
    CONFIG_STACK.pop()
    cucumber_json.unconfigure(config)


def pytest_generate_tests(metafunc: Metafunc):
    with suppress(AttributeError):
        metafunc.function.__pytest_bdd_scenario_registry__.parametrize(metafunc)


def pytest_cmdline_main(config: Config) -> int | None:
    return generation.cmdline_main(config)


@pytest.mark.trylast
def pytest_bdd_convert_tag_to_marks(feature, scenario, tag) -> Collection[Mark | MarkDecorator] | None:
    return [getattr(pytest.mark, tag)]


def pytest_bdd_match_step_definition_to_step(request, feature, scenario, step, previous_step) -> StepHandler.Definition:
    step_registry: StepHandler.Registry = request.getfixturevalue("step_registry")
    step_matcher: StepHandler.Matcher = request.getfixturevalue("step_matcher")

    return step_matcher(feature, scenario, step, previous_step, step_registry)
