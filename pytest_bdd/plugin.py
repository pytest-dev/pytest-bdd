"""Pytest plugin entry point. Used for any fixtures needed."""
from __future__ import annotations

from collections import deque
from contextlib import suppress
from functools import partial
from inspect import signature
from itertools import chain, filterfalse, starmap, tee
from operator import attrgetter, contains, methodcaller
from pathlib import Path
from types import ModuleType
from typing import Any, Collection, Iterable
from unittest.mock import patch
from urllib.parse import urlparse

import py
import pytest
from _pytest.nodes import Collector

from pytest_bdd import cucumber_json, generation, gherkin_terminal_reporter, given, steps, then, when
from pytest_bdd.allure_logging import AllurePytestBDD
from pytest_bdd.collector import FeatureFileModule as FeatureFileCollector
from pytest_bdd.collector import Module as ModuleCollector
from pytest_bdd.message_plugin import MessagePlugin
from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.model import Feature
from pytest_bdd.model.messages import Pickle
from pytest_bdd.model.messages import PickleStep as Step
from pytest_bdd.parser import GherkinParser
from pytest_bdd.reporting import ScenarioReporterPlugin
from pytest_bdd.runner import ScenarioRunner
from pytest_bdd.scenario import FeaturePathType, FileScenarioLocator, UrlScenarioLocator
from pytest_bdd.scenario import add_options as scenario_add_options
from pytest_bdd.scenario import scenarios
from pytest_bdd.steps import StepHandler
from pytest_bdd.struct_bdd.plugin import StructBDDPlugin
from pytest_bdd.typing.pytest import PYTEST7, Config, Mark, MarkDecorator, Metafunc, Parser, PytestPluginManager
from pytest_bdd.utils import IdGenerator, compose, getitemdefault, setdefaultattr


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
    parser.addini("bdd_features_base_url", "Base features url.")


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
    config.pluginmanager.register(StructBDDPlugin())


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


def _build_filter(filter_):
    if callable(filter_):
        updated_filter = filter_
    else:
        if filter_ is None:
            updated_filter = None
        else:
            if not isinstance(filter_, str):
                filter_ = str(filter_)

            def updated_filter(config, feature, scenario):
                return scenario.name == filter_

    return updated_filter


def _build_scenario_locators_from_mark(mark: Mark, config: Config) -> Iterable[Any]:
    raw_mark_arguments = signature(scenarios).bind(*mark.args, **mark.kwargs)
    raw_mark_arguments.apply_defaults()
    mark_arguments = raw_mark_arguments.arguments

    locators_iterables = [mark_arguments["locators"]]

    filter_ = _build_filter(getitemdefault(mark_arguments, "filter_", default=None))

    features_base_dir = mark.kwargs.get("features_base_dir")
    if features_base_dir is None:
        try:
            features_base_dir = config.getini("bdd_features_base_dir")
        except (ValueError, KeyError):
            features_base_dir = config.rootpath
    if callable(features_base_dir):
        features_base_dir = features_base_dir(config)

    features_base_url = mark.kwargs.get("features_base_url")
    if features_base_url is None:
        try:
            features_base_url = config.getini("bdd_features_base_url")
        except (ValueError, KeyError):
            features_base_url = None
    if callable(features_base_url):
        features_base_url = features_base_url(config)

    features_path_type = mark_arguments["features_path_type"]
    if features_path_type is None:
        features_path_type = FeaturePathType.UNDEFINED
    elif isinstance(features_path_type, str):
        features_path_type = FeaturePathType(features_path_type)
    elif isinstance(features_path_type, FeaturePathType):
        pass
    else:
        raise ValueError(f"Unknown feature path type")

    feature_paths = mark_arguments["feature_paths"]
    if feature_paths is None:
        feature_paths = []

    feature_paths_gen_1, feature_paths_gen_2 = tee(iter(feature_paths), 2)

    def is_valid_local_url(urllike: str):
        try:
            return not any(attrgetter("scheme", "netloc")(urlparse(urllike)))
        except ValueError:
            return False

    def is_valid_local_path(pathlike):
        return Path(pathlike).exists()

    def is_local_path(pathlike: Path | str):
        if features_path_type is FeaturePathType.PATH:
            return True
        elif features_path_type is FeaturePathType.URL:
            return False
        if is_valid_local_url(str(pathlike)):
            return True
        else:
            return is_valid_local_path(pathlike)

    path_locator = FileScenarioLocator(  # type: ignore[call-arg]
        feature_paths=filter(is_local_path, feature_paths_gen_1),
        filter_=filter_,
        encoding=mark_arguments["encoding"],
        features_base_dir=features_base_dir,
        mimetype=mark_arguments["features_mimetype"],
        parser_type=mark_arguments["parser_type"],
        parse_args=mark_arguments["parse_args"],
    )

    locators_iterables.append([path_locator])

    url_locator = UrlScenarioLocator(  # type: ignore[call-arg]
        url_paths=filterfalse(is_local_path, feature_paths_gen_2),
        filter_=mark_arguments["filter_"],
        encoding=mark_arguments["encoding"],
        features_base_url=features_base_url,
        mimetype=mark_arguments["features_mimetype"],
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


chain_map = compose(chain.from_iterable, map)


def pytest_generate_tests(metafunc: Metafunc):
    config = metafunc.config

    # build marker locators
    marks: list[Mark] = metafunc.definition.own_markers
    mark_names = list(map(attrgetter("name"), marks))
    if "pytest_bdd_scenario" in mark_names:
        scenario_marks = filter(lambda mark: mark.name == "scenarios", marks)
        locators = chain_map(partial(_build_scenario_locators_from_mark, config=config), scenario_marks)
        resolved_locators = chain_map(methodcaller("resolve", config), locators)

        metafunc.parametrize(
            "feature, scenario",
            starmap(partial(_build_scenario_param, config=config), resolved_locators),
        )


def pytest_cmdline_main(config: Config) -> int | None:
    return generation.cmdline_main(config)


def pytest_collect_file(parent: Collector, path, file_path=None):
    file_path = file_path or Path(path)
    config = parent.session.config
    is_enabled_feature_autoload = config.getoption("feature_autoload")
    if is_enabled_feature_autoload is None:
        is_enabled_feature_autoload = config.getini("feature_autoload")
    if not is_enabled_feature_autoload:
        return

    config = parent.config
    hook = parent.config.hook

    if hook.pytest_bdd_is_collectible(config=config, path=Path(file_path)):
        if hasattr(FeatureFileCollector, "from_parent"):
            collector = FeatureFileCollector.from_parent(
                parent, **(dict(path=Path(file_path)) if PYTEST7 else dict(fspath=py.path.local(file_path)))
            )
        else:
            collector = FeatureFileCollector(parent=parent, fspath=py.path.local(file_path))

        return collector


@pytest.mark.trylast
def pytest_bdd_convert_tag_to_marks(feature, scenario, tag) -> Collection[Mark | MarkDecorator] | None:
    return [getattr(pytest.mark, tag)]


def pytest_bdd_match_step_definition_to_step(request, feature, scenario, step, previous_step) -> StepHandler.Definition:
    step_registry: StepHandler.Registry = request.getfixturevalue("step_registry")
    step_matcher: StepHandler.Matcher = request.getfixturevalue("step_matcher")

    return step_matcher(feature, scenario, step, previous_step, step_registry)


def pytest_bdd_get_mimetype(config: Config, path: Path):
    if str(path).endswith(".gherkin") or str(path).endswith(".feature"):
        return Mimetype.gherkin_plain.value


def pytest_bdd_get_parser(config: Config, mimetype: str):
    return {Mimetype.gherkin_plain.value: GherkinParser}.get(mimetype)


def pytest_bdd_is_collectible(config: Config, path: Path):
    if any(map(partial(contains, {".gherkin", ".feature"}), path.suffixes)):
        return True
