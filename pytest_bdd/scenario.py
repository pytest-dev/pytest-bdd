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
from typing import TYPE_CHECKING, Sequence

import pytest
from _pytest.config import Config
from _pytest.python import Metafunc
from attr import Factory, attrib, attrs

from .model import Feature, Scenario
from .utils import get_caller_module_locals, get_caller_module_path, make_python_name

if TYPE_CHECKING:  # pragma: no cover
    from typing import Iterable


FakeRequest = collections.namedtuple("FakeRequest", ["module"])


@attrs
class ModuleScenarioRegistry:
    @attrs
    class ScenarioLocator:
        feature_paths = attrib(default=Factory(list))
        scenario_name = attrib(default=None)
        encoding = attrib(default="utf-8")
        features_base_dir = attrib(default=None)
        parser = attrib(default=None)

    caller_locals = attrib()
    caller_module_path = attrib()
    locator_registry: list[tuple] = attrib(default=Factory(list))
    resolved_locator_registry: dict = attrib(default=Factory(dict))
    resolved = attrib(default=False)
    config = attrib(default=None)

    @classmethod
    def get(
        cls,
        caller_locals,
        caller_module_path,
    ):
        if "__pytest_bdd_scenario_registry__" not in caller_locals.keys():
            caller_locals["__pytest_bdd_scenario_registry__"] = ModuleScenarioRegistry(
                caller_locals=caller_locals, caller_module_path=caller_module_path
            )
        return caller_locals["__pytest_bdd_scenario_registry__"]

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
                for feature, scenario in self.resolve_locator(locator):
                    self.resolved_locator_registry[(feature.uri, scenario.id)] = test_func, feature, scenario
        return self.resolved_locator_registry

    def resolve_locator(self, locator: ModuleScenarioRegistry.ScenarioLocator):
        features_base_dir = locator.features_base_dir
        if features_base_dir is None:
            features_base_dir = self.features_base_dir
        features_base_dir = (Path.cwd() / Path(features_base_dir)).resolve()

        def feature_paths_gen():
            for feature_path in map(Path, locator.feature_paths):
                if feature_path.is_dir():
                    yield from feature_path.rglob("*.feature")
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

            feature = Feature.get_from_path(
                features_base_dir=features_base_dir,
                filename=rel_feature_path,
                encoding=locator.encoding,
                parser=locator.parser,
            )

            for scenario in feature.scenarios:
                if locator.scenario_name is None or locator.scenario_name == scenario.name:
                    yield feature, scenario

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
    feature_name: Path | str,
    scenario_name: str,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    return_test_decorator=True,
    _caller_module_locals=None,
    _caller_module_path=None,
    _parser=None,
):
    """
    Scenario decorator.

    :param feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param scenario_name: Scenario name.
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param return_test_decorator; Return test decorator or generated test
    """
    return _scenarios(
        feature_paths=[feature_name],
        scenario_name=scenario_name,
        encoding=encoding,
        features_base_dir=features_base_dir,
        return_test_decorator=return_test_decorator,
        _caller_module_locals=_caller_module_locals or get_caller_module_locals(depth=2),
        _caller_module_path=_caller_module_path or get_caller_module_path(depth=2),
        _parser=_parser,
    )


def scenarios(
    *feature_paths: Path | str,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    return_test_decorator=True,
    _caller_module_locals=None,
    _caller_module_path=None,
    _parser=None,
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
        scenario_name=None,
        encoding=encoding,
        features_base_dir=features_base_dir,
        return_test_decorator=return_test_decorator,
        _caller_module_locals=_caller_module_locals or get_caller_module_locals(depth=2),
        _caller_module_path=_caller_module_path or get_caller_module_path(depth=2),
        _parser=_parser,
    )


def _scenarios(
    feature_paths: Sequence[Path | str],
    scenario_name: str | None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    return_test_decorator=True,
    _caller_module_locals=None,
    _caller_module_path=None,
    _parser=None,
):
    """
    Scenario decorator.

    :param feature_paths: Features file names. Absolute or relative to the configured feature base path.
    :param scenario_name: Scenario name.
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param return_test_decorator; Return test decorator or generated test
    """
    scenario_locator = ModuleScenarioRegistry.ScenarioLocator(  # type: ignore[call-arg]
        feature_paths=feature_paths,
        scenario_name=scenario_name,
        encoding=encoding,
        features_base_dir=features_base_dir,
        parser=_parser,
    )
    module_scenario_registry = ModuleScenarioRegistry.get(
        caller_locals=_caller_module_locals,
        caller_module_path=_caller_module_path,
    )

    @pytest.mark.pytest_bdd_scenario
    @pytest.mark.usefixtures("feature", "scenario")
    def test():
        ...

    test.__name__ = next(iter(test_names))

    module_scenario_registry.add(scenario_locator, test)

    def decorator(func):
        updated_func = pytest.mark.pytest_bdd_scenario(pytest.mark.usefixtures("feature", "scenario")(func))
        module_scenario_registry.update(scenario_locator, test, updated_func)
        return updated_func

    return decorator if return_test_decorator else test
