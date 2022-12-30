"""Pytest plugin entry point. Used for any fixtures needed."""
from __future__ import annotations

from collections import deque
from contextlib import suppress
from functools import partial
from inspect import signature
from itertools import chain
from operator import attrgetter, contains, methodcaller
from pathlib import Path
from types import ModuleType
from typing import Any, Collection, Iterable
from unittest.mock import patch

import py
import pytest

from pytest_bdd import cucumber_json, generation, gherkin_terminal_reporter, given, steps, then, when
from pytest_bdd.allure_logging import AllurePytestBDD
from pytest_bdd.collector import FeatureFileModule as FeatureFileCollector
from pytest_bdd.collector import Module as ModuleCollector
from pytest_bdd.message_plugin import MessagePlugin
from pytest_bdd.model import Feature
from pytest_bdd.model.messages import Pickle
from pytest_bdd.model.messages import PickleStep as Step
from pytest_bdd.reporting import ScenarioReporterPlugin
from pytest_bdd.runner import ScenarioRunner
from pytest_bdd.scenario import FileScenarioLocator, _scenarios
from pytest_bdd.scenario import add_options as scenario_add_options
from pytest_bdd.steps import StepHandler
from pytest_bdd.typing.pytest import PYTEST7, Config, Mark, MarkDecorator, Metafunc, Parser, PytestPluginManager
from pytest_bdd.typing.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.utils import IdGenerator, setdefaultattr


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
    MessagePlugin.add_options(parser)


def add_bdd_ini(parser: Parser) -> None:
    parser.addini("bdd_features_base_dir", "Base features directory.")


@pytest.mark.trylast
def pytest_configure(config: Config) -> None:
    """Configure all subplugins."""
    config.addinivalue_line("markers", "pytest_bdd_scenario: marker to identify pytest_bdd tests")
    config.addinivalue_line("markers", "scenarios: marker to provide scenarios locator")
    cucumber_json.configure(config)
    gherkin_terminal_reporter.configure(config)
    config.pluginmanager.register(ScenarioReporterPlugin())
    config.pluginmanager.register(ScenarioRunner())
    config.pluginmanager.register(MessagePlugin(config=config), name="pytest_bdd_messages")  # type: ignore[call-arg]
    config.__allure_plugin__ = AllurePytestBDD.register_if_allure_accessible(config)  # type: ignore[attr-defined]
    setdefaultattr(config, "pytest_bdd_id_generator", value_factory=IdGenerator)


@pytest.mark.tryfirst
def pytest_unconfigure(config: Config) -> None:
    config.pluginmanager.unregister(name="pytest_bdd_messages")
    with suppress(AttributeError):
        config.__allure_plugin__.unregister(config)  # type: ignore[attr-defined]
    cucumber_json.unconfigure(config)


@pytest.hookimpl(hookwrapper=True)
def pytest_pycollect_makemodule(path, parent, module_path=None):
    with patch("_pytest.python.Module", new=ModuleCollector):
        yield


@pytest.hookimpl(tryfirst=True)
def pytest_plugin_registered(plugin, manager):
    if hasattr(plugin, "__file__") and isinstance(plugin, (type, ModuleType)):
        StepHandler.Registry.inject_registry_fixture_and_register_steps(plugin)


def _build_scenario_locators_from_mark(mark: Mark, config: Config) -> Iterable[Any]:
    raw_mark_arguments = signature(_scenarios).bind(*mark.args, **mark.kwargs)
    raw_mark_arguments.apply_defaults()
    mark_arguments = raw_mark_arguments.arguments

    locators_iterables = [mark_arguments["locators"]]

    if mark_arguments["feature_paths"]:
        try:
            features_base_dir = mark.kwargs.get("features_base_dir", config.getini("bdd_features_base_dir"))
        except (ValueError, KeyError):
            features_base_dir = config.rootpath
        if callable(features_base_dir):
            features_base_dir = features_base_dir(config)

        path_locator = FileScenarioLocator(  # type: ignore[call-arg]
            feature_paths=mark_arguments["feature_paths"],
            filter_=mark_arguments["filter_"],
            encoding=mark_arguments["encoding"],
            features_base_dir=features_base_dir,
            parser_type=mark_arguments["parser_type"],
            parse_args=mark_arguments["parse_args"],
        )

        locators_iterables.append([path_locator])

    if mark_arguments["features_base_url"]:
        features_base_url = mark.kwargs.get("features_base_url", config.getini("bdd_features_base_url"))
        if callable(features_base_url):
            features_base_url = features_base_url(config)

        url_locator = UrlScenarioLocator(  # type: ignore[call-arg, name-defined]
            url_paths=mark_arguments["url_paths"],
            filter_=mark_arguments["filter_"],
            encoding=mark_arguments["encoding"],
            features_base_url=features_base_url,
            parser_type=mark_arguments["parser_type"],
            parse_args=mark_arguments["parse_args"],
        )

        locators_iterables.append([url_locator])
    return chain(*locators_iterables)


def _build_scenario_param(feature: Feature, pickle: Pickle, config: Config):
    marks = []
    for tag in feature._get_pickle_tag_names(pickle):
        tag_marks = config.hook.pytest_bdd_convert_tag_to_marks(feature=feature, scenario=pickle, tag=tag)
        if tag_marks is not None:
            marks.extend(tag_marks)
    return pytest.param(
        feature,
        pickle,
        id=f"{feature.uri}-{feature.name}-{pickle.name}{feature.build_pickle_table_rows_breadcrumb(pickle)}",
        marks=marks,
    )


def pytest_generate_tests(metafunc: Metafunc):
    config = metafunc.config

    # build marker locators
    marks: list[Mark] = metafunc.definition.own_markers
    if "pytest_bdd_scenario" in list(map(attrgetter("name"), marks)):
        scenario_marks = filter(lambda mark: mark.name == "scenarios", marks)

        locators = chain.from_iterable(
            map(lambda mark: _build_scenario_locators_from_mark(mark, config), scenario_marks)
        )
        resolved_locators = chain.from_iterable(map(methodcaller("resolve", config), locators))

        metafunc.parametrize(
            "feature, scenario",
            [_build_scenario_param(feature, pickle, config) for feature, pickle in resolved_locators],
        )


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
            collector = FeatureFileCollector.from_parent(
                parent, **(dict(path=Path(file_path)) if PYTEST7 else dict(fspath=py.path.local(file_path)))
            )
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
                collector.parser_type = partial(StructBDDParser, kind=struct_bdd_parser_kind)

        return collector


@pytest.mark.trylast
def pytest_bdd_convert_tag_to_marks(feature, scenario, tag) -> Collection[Mark | MarkDecorator] | None:
    return [getattr(pytest.mark, tag)]


def pytest_bdd_match_step_definition_to_step(request, feature, scenario, step, previous_step) -> StepHandler.Definition:
    step_registry: StepHandler.Registry = request.getfixturevalue("step_registry")
    step_matcher: StepHandler.Matcher = request.getfixturevalue("step_matcher")

    return step_matcher(feature, scenario, step, previous_step, step_registry)
