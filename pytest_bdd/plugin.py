"""Pytest plugin entry point. Used for any fixtures needed."""
from __future__ import annotations

from collections import deque
from contextlib import suppress
from functools import partial
from operator import attrgetter, contains, methodcaller
from pathlib import Path
from types import ModuleType
from typing import Collection
from unittest.mock import patch

import py
import pytest

from pytest_bdd import cucumber_json, generation, gherkin_terminal_reporter, given, steps, then, when
from pytest_bdd.allure_logging import AllurePytestBDD
from pytest_bdd.collector import FeatureFileModule as FeatureFileCollector
from pytest_bdd.collector import Module as ModuleCollector
from pytest_bdd.model import Step
from pytest_bdd.reporting import ScenarioReporterPlugin
from pytest_bdd.runner import ScenarioRunner
from pytest_bdd.scenario import add_options as scenario_add_options
from pytest_bdd.steps import StepHandler
from pytest_bdd.typing.pytest import Config, Mark, MarkDecorator, Metafunc, Parser, PytestPluginManager
from pytest_bdd.typing.struct_bdd import STRUCT_BDD_INSTALLED


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


__registry = StepHandler.Registry()


@pytest.fixture
def step_registry() -> StepHandler.Registry:
    """Fixture containing registry of all user-defined steps"""
    return __registry


step_registry.__registry__ = __registry  # type: ignore[attr-defined]


@pytest.fixture
def step_matcher(pytestconfig) -> StepHandler.Matcher:
    """Fixture containing matcher to help find step definition for selected step of scenario"""
    return StepHandler.Matcher(pytestconfig)  # type: ignore[call-arg]


@pytest.fixture
def steps_left() -> deque[Step]:
    """Fixture containing steps which are left to be executed"""
    return deque()


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    add_bdd_ini(parser)
    steps.add_options(parser)
    scenario_add_options(parser)
    cucumber_json.add_options(parser)
    generation.add_options(parser)
    gherkin_terminal_reporter.add_options(parser)


def add_bdd_ini(parser: Parser) -> None:
    parser.addini("bdd_features_base_dir", "Base features directory.")


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    config.addinivalue_line("markers", "pytest_bdd_scenario: marker to identify pytest_bdd tests")
    cucumber_json.configure(config)
    gherkin_terminal_reporter.configure(config)
    config.pluginmanager.register(ScenarioReporterPlugin())
    config.pluginmanager.register(ScenarioRunner())
    AllurePytestBDD.register_if_allure_accessible(config)


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makemodule(path, parent, module_path=None):
    with patch("_pytest.python.Module", new=ModuleCollector):
        yield


@pytest.hookimpl(tryfirst=True)
def pytest_plugin_registered(plugin, manager):
    if hasattr(plugin, "__file__") and isinstance(plugin, (type, ModuleType)):
        StepHandler.Registry.inject_registry_fixture_and_register_steps(plugin)


def pytest_unconfigure(config: Config) -> None:
    """Unconfigure all subplugins."""
    cucumber_json.unconfigure(config)


def pytest_generate_tests(metafunc: Metafunc):
    with suppress(AttributeError):
        metafunc.function.__pytest_bdd_scenario_registry__.parametrize(metafunc)


def pytest_cmdline_main(config: Config) -> int | None:
    return generation.cmdline_main(config)


def pytest_collect_file(parent, path, file_path=None):
    file_path = file_path or Path(path)
    config = parent.session.config
    is_enabled_feature_autoload = config.getoption("feature_autoload")
    if is_enabled_feature_autoload is None:
        is_enabled_feature_autoload = config.getini("feature_autoload")
    if not is_enabled_feature_autoload:
        return
    if any(map(partial(contains, {".gherkin", ".feature"}), file_path.suffixes)):
        if hasattr(FeatureFileCollector, "from_parent"):
            collector = FeatureFileCollector.from_parent(parent, fspath=py.path.local(file_path))
        else:
            collector = FeatureFileCollector(parent=parent, fspath=py.path.local(file_path))

        if STRUCT_BDD_INSTALLED:
            from pytest_bdd.struct_bdd.parser import StructBDDParser

            struct_bdd_parser_kind = next(
                filter(
                    partial(contains, list(map(methodcaller("strip", "."), file_path.suffixes))),
                    list(map(attrgetter("value"), StructBDDParser.KIND)),
                ),
                None,
            )

            if struct_bdd_parser_kind is not None:
                collector.parser = StructBDDParser(kind=struct_bdd_parser_kind)

        return collector


@pytest.mark.trylast
def pytest_bdd_convert_tag_to_marks(feature, scenario, tag) -> Collection[Mark | MarkDecorator] | None:
    return [getattr(pytest.mark, tag)]


def pytest_bdd_match_step_definition_to_step(request, feature, scenario, step, previous_step) -> StepHandler.Definition:
    step_registry: StepHandler.Registry = request.getfixturevalue("step_registry")
    step_matcher: StepHandler.Matcher = request.getfixturevalue("step_matcher")

    return step_matcher(feature, scenario, step, previous_step, step_registry)
