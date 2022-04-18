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
import os
import re
import sys
from functools import reduce
from operator import truediv
from os.path import commonpath
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from _pytest.config import Config
from _pytest.fixtures import FixtureRequest

from . import exceptions
from .model import Feature, Scenario
from .steps import StepHandler
from .utils import CONFIG_STACK, get_args, get_caller_module_locals, get_caller_module_path

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable, Iterable

    from .types import TestFunc

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")


@runtime_checkable
class StepFunc(Protocol):
    target_fixtures: list[str]


def _execute_scenario(feature: Feature, scenario: Scenario, request):
    """Execute the scenarios.

    :param feature: Feature.
    :param scenario: Scenario.
    :param request: request.
    :param encoding: Encoding.
    """
    request.config.hook.pytest_bdd_before_scenario(request=request, feature=feature, scenario=scenario)

    try:
        previous_step = None
        for step in scenario.steps:
            StepHandler.Executor(
                request=request, feature=feature, scenario=scenario, step=step, previous_step=previous_step
            ).execute()  # type: ignore[call-arg]
            previous_step = step
    finally:
        request.config.hook.pytest_bdd_after_scenario(request=request, feature=feature, scenario=scenario)


FakeRequest = collections.namedtuple("FakeRequest", ["module"])


def _build_scenario_param(feature: Feature, scenario: Scenario, config: Config):
    marks = []
    for tag in scenario.tag_names:
        tag_marks = config.hook.pytest_bdd_convert_tag_to_marks(feature=feature, scenario=scenario, tag=tag)
        if tag_marks is not None:
            marks.extend(tag_marks)
    return pytest.param(scenario, id=f"{scenario.name}{scenario.table_rows_breadcrumb}", marks=marks)


def _get_scenario_decorator(
    feature: Feature,
    scenarios: list[Scenario],
):
    # HACK: Ideally we would use `def decorator(fn)`, but we want to return a custom exception
    # when the decorator is misused.
    # Pytest inspect the signature to determine the required fixtures, and in that case it would look
    # for a fixture called "fn" that doesn't exist (if it exists then it's even worse).
    # It will error with a "fixture 'fn' not found" message instead.
    # We can avoid this hack by using a pytest hook and check for misuse instead.
    def decorator(*args: Callable) -> TestFunc:
        if not args:
            raise exceptions.ScenarioIsDecoratorOnly(
                "scenario function can only be used as a decorator. Refer to the documentation."
            )
        [fn] = args
        fn_args = get_args(fn)

        test_function: TestFunc

        # TODO investigate other approach to pass config
        config = CONFIG_STACK[-1]

        @pytest.mark.parametrize("scenario", [_build_scenario_param(feature, scenario, config) for scenario in scenarios])  # type: ignore[no-redef]
        @pytest.mark.parametrize("feature", [pytest.param(feature, id=f"{feature.uri}-{feature.name}")])
        # We need to tell pytest that the original function requires its fixtures,
        # otherwise indirect fixtures would not work.
        @pytest.mark.usefixtures(*fn_args)
        def test_function(request: FixtureRequest, feature, scenario) -> Any:
            _execute_scenario(feature, scenario, request)
            fixture_values = [request.getfixturevalue(arg) for arg in fn_args]
            return fn(*fixture_values)

        # region TODO potential bug for scenarios with same name
        test_function.__doc__ = f"{feature.uri}: {scenarios[0].name} {scenarios[0].id}"
        test_function.__scenario__ = scenarios[0]
        # endregion

        return cast("TestFunc", test_function)

    return decorator


def scenario(
    feature_name: Path | str,
    scenario_name: str,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
):
    """Scenario decorator.

    :param feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param scenario_name: Scenario name.
    :param encoding: Feature file encoding.
    """

    scenario_name = str(scenario_name)
    caller_module_path = get_caller_module_path()

    # Get the feature
    if features_base_dir is None:
        features_base_dir = get_features_base_dir(caller_module_path)
    features_base_dir = (Path.cwd() / Path(features_base_dir)).resolve()

    # TODO: possibility to use alternate parsers
    feature = Feature.get_from_path(features_base_dir, feature_name, encoding=encoding)

    scenarios = list(filter(lambda scenario: scenario.name == scenario_name, feature.scenarios))
    if not scenarios:
        feature_name = feature.name or "[Empty]"
        raise exceptions.ScenarioNotFound(
            f'Scenario "{scenario_name}" in feature "{feature_name}" in {feature.filename} is not found.'
        )

    return _get_scenario_decorator(feature=feature, scenarios=scenarios)


def get_features_base_dir(caller_module_path: str) -> Path:
    default_base_dir = os.path.dirname(caller_module_path)
    return Path(get_from_ini("bdd_features_base_dir", default_base_dir))


def get_from_ini(key: str, default: str) -> str:
    """Get value from ini config. Return default if value has not been set.

    Use if the default value is dynamic. Otherwise set default on addini call.
    """
    config = CONFIG_STACK[-1]
    value = config.getini(key)
    if not isinstance(value, str):
        raise TypeError(f"Expected a string for configuration option {value!r}, got a {type(value)} instead")
    return value if value != "" else default


def make_python_name(string: str) -> str:
    """Make python attribute name out of a given string."""
    string = re.sub(PYTHON_REPLACE_REGEX, "", string.replace(" ", "_"))
    return re.sub(ALPHA_REGEX, "", string).lower()


def make_python_docstring(string: str) -> str:
    """Make a python docstring literal out of a given string."""
    return '"""{}."""'.format(string.replace('"""', '\\"\\"\\"'))


def make_string_literal(string: str) -> str:
    """Make python string literal out of a given string."""
    return "'{}'".format(string.replace("'", "\\'"))


def get_python_name_generator(name: str) -> Iterable[str]:
    """Generate a sequence of suitable python names out of given arbitrary string name."""
    python_name = make_python_name(name)
    suffix = ""
    index = 0

    def get_name() -> str:
        return f"test_{python_name}{suffix}"

    while True:
        yield get_name()
        index += 1
        suffix = f"_{index}"


def scenarios(*feature_paths: str | Path, **kwargs: Any) -> None:
    """Parse features from the paths and put all found scenarios in the caller module.

    :param *feature_paths: feature file paths to use for scenarios
    """
    caller_locals = get_caller_module_locals()
    caller_path = get_caller_module_path()

    features_base_dir = kwargs.get("features_base_dir")
    if features_base_dir is None:
        features_base_dir = get_features_base_dir(caller_path)
    features_base_dir = (Path.cwd() / Path(features_base_dir)).resolve()

    abs_feature_paths = []
    for path in feature_paths:
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(features_base_dir, path))
        abs_feature_paths.append(path)

    rel_feature_paths = []
    for path in map(Path, feature_paths):
        if path.is_absolute():
            try:
                common_path = Path(commonpath([path, features_base_dir]))
            except ValueError:
                rel_feature_paths.append(path)
            else:
                sub_levels = len(features_base_dir.relative_to(common_path).parts)
                sub_path = reduce(truediv, map(Path, [".."] * sub_levels), Path())
                rel_feature_paths.append(sub_path / path.relative_to(common_path))
        else:
            rel_feature_paths.append(path)

    found = False

    module_scenarios = frozenset(
        (attr.__scenario__.feature.filename, attr.__scenario__.name)
        for name, attr in caller_locals.items()
        if hasattr(attr, "__scenario__")
    )

    for feature in Feature.get_from_paths(rel_feature_paths, features_base_dir=features_base_dir):
        for scenario_object in feature.scenarios:
            scenario_name = scenario_object.name
            # skip already bound scenarios
            if (feature.filename, scenario_name) not in module_scenarios:

                @scenario(feature.uri, scenario_name, **{**kwargs, **dict(features_base_dir=features_base_dir)})
                def _scenario() -> None:
                    pass  # pragma: no cover

                for test_name in get_python_name_generator(scenario_name):
                    if test_name not in caller_locals:
                        # found an unique test name
                        caller_locals[test_name] = _scenario
                        break
            found = True
    if not found:
        raise exceptions.NoScenariosFound(abs_feature_paths)
