"""Scenario implementation.

The pytest will collect the test case and the steps will be executed
line by line.

Example:

test_publish_article = scenario(
    feature_name="publish_article.feature",
    scenario_name="Publishing the article",
)
"""
from __future__ import annotations

import collections
from functools import reduce
from operator import truediv
from os.path import commonpath, dirname
from pathlib import Path
from typing import Callable, Iterable, Sequence, cast

import pytest
from attr import Factory, attrib, attrs

from pytest_bdd.model import Feature, Scenario
from pytest_bdd.parser import GherkinParser
from pytest_bdd.typing.parser import ParserProtocol
from pytest_bdd.typing.pytest import Config, Metafunc
from pytest_bdd.utils import get_caller_module_locals, get_caller_module_path, make_python_name

Args = collections.namedtuple("Args", ["args", "kwargs"])
FakeRequest = collections.namedtuple("FakeRequest", ["module"])


@attrs
class FileScenarioLocator:
    feature_paths = attrib(default=Factory(list))
    scenario_filter = attrib(default=None)
    encoding = attrib(default="utf-8")
    features_base_dir = attrib(default=None)
    parser: ParserProtocol = attrib(default=Factory(GherkinParser))
    parse_args: Args = attrib(default=Factory(lambda: Args((), {})))

    @property
    def glob(self):
        return self.parser.glob

    def resolve(self):
        features_base_dir = (
            self.features_base_dir() if isinstance(self.features_base_dir, Callable) else self.features_base_dir
        )
        features_base_dir = (Path.cwd() / Path(features_base_dir)).resolve()

        already_resolved = set()

        def feature_paths_gen():
            for feature_path in map(Path, self.feature_paths):
                if feature_path.is_dir():
                    yield from iter(self.glob(feature_path))
                else:
                    yield feature_path

        for feature_path in feature_paths_gen():
            if feature_path.is_absolute():
                try:
                    common_path = Path(commonpath([feature_path, features_base_dir]))
                except ValueError:
                    rel_feature_path = feature_path
                else:
                    sub_levels = len(features_base_dir.relative_to(common_path).parts)
                    sub_path = reduce(truediv, [".."] * sub_levels, Path())
                    rel_feature_path = sub_path / feature_path.relative_to(common_path)
            else:
                rel_feature_path = feature_path

            uri = str(rel_feature_path.as_posix())
            absolute_feature_path = (Path(features_base_dir) / rel_feature_path).resolve()

            if absolute_feature_path not in already_resolved:
                already_resolved.add(absolute_feature_path)

                feature = self.parser.parse(
                    absolute_feature_path,
                    uri,
                    *self.parse_args.args,
                    **{**dict(encoding=self.encoding), **self.parse_args.kwargs},
                )

                for scenario in feature.scenarios:
                    if self.scenario_filter is None or self.scenario_filter(feature, scenario):
                        yield feature, scenario


@attrs
class ModuleScenarioRegistry:

    caller_locals = attrib()
    caller_module_path = attrib()
    locator_registry: list[tuple] = attrib(default=Factory(list))
    resolved_locator_registry: dict = attrib(default=Factory(dict))
    resolved = attrib(default=False)
    config = attrib(default=None)

    @classmethod
    def get(
        cls,
        caller_locals: dict | None = None,
        caller_module_path: str = None,
    ) -> ModuleScenarioRegistry:
        caller_locals = cast(dict, caller_locals if caller_locals is not None else get_caller_module_locals(depth=2))
        caller_module_path = cast(
            str, caller_module_path if caller_module_path is not None else get_caller_module_path(depth=2)
        )
        if "__pytest_bdd_scenario_registry__" not in caller_locals.keys():
            caller_locals["__pytest_bdd_scenario_registry__"] = ModuleScenarioRegistry(  # type: ignore[call-arg]
                caller_locals=caller_locals, caller_module_path=caller_module_path
            )
        return cast(ModuleScenarioRegistry, caller_locals["__pytest_bdd_scenario_registry__"])

    def add(self, locator, test_func):
        test_func.__pytest_bdd_scenario_registry__ = self
        self.locator_registry.append((locator, test_func))
        if test_func.__name__ not in self.caller_locals.keys():
            self.caller_locals[test_func.__name__] = test_func

    def update(self, locator, updatable, test_func):
        for index, (registry_locator, registry_test_func) in enumerate(self.locator_registry):
            if locator == registry_locator:
                del self.caller_locals[updatable.__name__]
                self.add(locator, test_func)
                break

    @property
    def resolved_locators(self):
        if not self.resolved:
            self.resolved = True
            for locator, test_func in self.locator_registry:
                for feature, scenario in locator.resolve():
                    self.resolved_locator_registry[(feature.uri, scenario.id)] = test_func, feature, scenario
        return self.resolved_locator_registry

    def parametrize(self, metafunc: Metafunc):
        test_func = metafunc.function
        self.config = metafunc.config

        parametrizations = [
            (feature, scenario) for _, (func, feature, scenario) in self.resolved_locators.items() if func is test_func
        ]

        metafunc.parametrize(
            "feature, scenario",
            [self._build_scenario_param(feature, scenario, self.config) for feature, scenario in parametrizations],
        )

    @staticmethod
    def _build_scenario_param(feature: Feature, scenario: Scenario, config: Config):
        marks = []
        for tag in scenario.tag_names:
            tag_marks = config.hook.pytest_bdd_convert_tag_to_marks(feature=feature, scenario=scenario, tag=tag)
            if tag_marks is not None:
                marks.extend(tag_marks)
        return pytest.param(
            feature,
            scenario,
            id=f"{feature.uri}-{feature.name}-{scenario.name}{scenario.table_rows_breadcrumb}",
            marks=marks,
        )

    @property
    def features_base_dir(self) -> Path:
        default_base_dir = dirname(self.caller_module_path)
        return Path(self.get_from_config_ini("bdd_features_base_dir", default_base_dir))

    def get_from_config_ini(self, key: str, default: str) -> str:
        """Get value from ini config. Return default if value has not been set.

        Use if the default value is dynamic. Otherwise set default on addini call.
        """
        value = self.config.getini(key)
        if not isinstance(value, str):
            raise TypeError(f"Expected a string for configuration option {value!r}, got a {type(value)} instead")
        return value if value != "" else default

    def build_bound_locator_test_function(self, locator):
        @pytest.mark.pytest_bdd_scenario
        @pytest.mark.usefixtures("feature", "scenario")
        def test():
            ...

        test.__name__ = next(iter(test_names))

        self.add(locator, test)

        return test

    def build_bound_locator_test_decorator(self, locator):
        def decorator(func):
            updated_func = pytest.mark.pytest_bdd_scenario(pytest.mark.usefixtures("feature", "scenario")(func))
            self.update(locator, self.build_bound_locator_test_function(locator), updated_func)
            return updated_func

        return decorator


def get_python_name_generator(name: str) -> Iterable[str]:
    """Generate a sequence of suitable python names out of given arbitrary string name."""
    python_name = make_python_name(name)
    suffix = ""
    index = 0

    def get_name() -> str:
        return "_".join(filter(bool, ["test", python_name, suffix]))

    while True:
        yield get_name()
        index += 1
        suffix = f"{index}"


test_names = get_python_name_generator("")


def scenario(
    feature_name: Path | str = Path(),
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    return_test_decorator=True,
    parser: ParserProtocol | None = None,
    parse_args=Args((), {}),
    _caller_module_locals=None,
    _caller_module_path=None,
):
    """
    Scenario decorator.

    :param feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param scenario_name: Scenario name.
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param return_test_decorator; Return test decorator or generated test
    :param parser: Parser used to parse feature-like file
    :param parse_args: args consumed by parser during parsing
    """
    return _scenarios(
        feature_paths=[feature_name],
        scenario_filter_or_scenario_name=scenario_name,
        encoding=encoding,
        features_base_dir=features_base_dir,
        return_test_decorator=return_test_decorator,
        _caller_module_locals=_caller_module_locals or get_caller_module_locals(depth=2),
        _caller_module_path=_caller_module_path or get_caller_module_path(depth=2),
        parser=parser,
        parse_args=parse_args,
    )


def scenarios(
    *feature_paths: Path | str,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    return_test_decorator=False,
    parser: ParserProtocol | None = None,
    parse_args=Args((), {}),
    _caller_module_locals=None,
    _caller_module_path=None,
):
    """
    Scenario decorator.

    :param feature_paths: Features file names. Absolute or relative to the configured feature base path.
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param return_test_decorator; Return test decorator or generated test
    """
    return _scenarios(
        feature_paths=feature_paths,
        scenario_filter_or_scenario_name=None,
        encoding=encoding,
        features_base_dir=features_base_dir,
        return_test_decorator=return_test_decorator,
        parser=parser,
        parse_args=parse_args,
        _caller_module_locals=_caller_module_locals or get_caller_module_locals(depth=2),
        _caller_module_path=_caller_module_path or get_caller_module_path(depth=2),
    )


def _scenarios(
    feature_paths: Sequence[Path | str],
    scenario_filter_or_scenario_name: str | Callable | None,
    return_test_decorator=True,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    parser: ParserProtocol | None = None,
    parse_args=Args((), {}),
    _caller_module_locals=None,
    _caller_module_path=None,
):
    if parser is None:
        parser = GherkinParser()
    module_scenario_registry = ModuleScenarioRegistry.get(
        caller_locals=_caller_module_locals,
        caller_module_path=_caller_module_path,
    )

    scenario_filter_kwarg = {}
    if isinstance(scenario_filter_or_scenario_name, str):
        scenario_filter_kwarg = {
            "scenario_filter": lambda feature, scenario: scenario.name == scenario_filter_or_scenario_name
        }
    if callable(scenario_filter_or_scenario_name):
        scenario_filter_kwarg = {"scenario_filter": scenario_filter_or_scenario_name}

    scenario_locator = FileScenarioLocator(  # type: ignore[call-arg]
        feature_paths=feature_paths,
        **scenario_filter_kwarg,
        encoding=encoding,
        features_base_dir=(
            features_base_dir if features_base_dir is not None else lambda: module_scenario_registry.features_base_dir
        ),  # known only after start of pytest runtime
        parser=parser,
        parse_args=parse_args,
    )

    return (
        module_scenario_registry.build_bound_locator_test_decorator
        if return_test_decorator
        else module_scenario_registry.build_bound_locator_test_function
    )(scenario_locator)
