"""Pytest plugin entry point. Used for any fixtures needed."""

from __future__ import annotations

import os
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING, TypeVar

import pytest
from typing_extensions import ParamSpec

from . import cucumber_json, generation, gherkin_terminal_reporter, given, reporting, then, when
from .feature import get_feature
from .scenario import get_features_base_dir, get_python_name_generator, scenario
from .utils import CONFIG_STACK

if TYPE_CHECKING:
    from _pytest.config import Config, PytestPluginManager
    from _pytest.config.argparsing import Parser
    from _pytest.nodes import Item
    from _pytest.runner import CallInfo
    from pluggy._result import _Result


P = ParamSpec("P")
T = TypeVar("T")


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
    Otherwise, pytest_bdd will add all the context variables in this fixture
    from the example definitions in the feature file.
    """
    return {}


def pytest_addoption(parser: Parser) -> None:
    """Add pytest-bdd options."""
    add_bdd_ini(parser)
    cucumber_json.add_options(parser)
    generation.add_options(parser)
    gherkin_terminal_reporter.add_options(parser)
    parser.addini("bdd_auto_collect_features", "Automatically collect feature files", type="bool", default=False)


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
    if CONFIG_STACK:
        CONFIG_STACK.pop()
    cucumber_json.unconfigure(config)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: Item, call: CallInfo) -> Generator[None, _Result, None]:
    outcome = yield
    reporting.runtest_makereport(item, call, outcome.get_result())


class FeatureFile(pytest.File):
    """Feature file collector."""

    def collect(self) -> list[pytest.Item]:
        """Collect scenarios from feature file."""
        if not self.config.getini("bdd_auto_collect_features"):
            return []

        items = []
        base_path = get_features_base_dir(str(self.config.rootpath))
        rel_path = os.path.relpath(str(self.fspath), base_path)

        try:
            feature = get_feature(base_path, rel_path)
        except Exception as e:
            self.config.warn("PytestBDD", f"Failed to parse feature file {self.fspath}: {e}")
            return []

        for scenario_name, _ in feature.scenarios.items():
            # Create test function using similar logic to scenarios()
            @scenario(
                rel_path,
                scenario_name,
                features_base_dir=base_path,
            )
            def test_auto_collected():
                """Auto-collected scenario."""
                pass

            # Generate unique test name
            for test_name in get_python_name_generator(scenario_name):
                test = pytest.Function.from_parent(self, name=test_name, callobj=test_auto_collected)
                items.append(test)
                break

        return items


def pytest_collect_file(parent: pytest.Collector, file_path: Path) -> pytest.Collector | None:
    """Collect feature files."""
    if file_path.suffix == ".feature":
        return FeatureFile.from_parent(parent, path=file_path)
    return None
