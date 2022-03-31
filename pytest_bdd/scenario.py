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
from typing import TYPE_CHECKING, cast
from warnings import warn

import pytest
from _pytest.fixtures import FixtureLookupError, FixtureRequest
from _pytest.warning_types import PytestDeprecationWarning

from . import exceptions
from .feature import get_feature, get_features
from .steps import Step
from .utils import CONFIG_STACK, DefaultMapping, apply_tag, get_args, get_caller_module_locals, get_caller_module_path

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable, Iterable

    from _pytest.mark.structures import ParameterSet

    from .parser import ExampleRowUnited, Feature, Scenario, ScenarioTemplate
    from .types import TestFunc

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")


@runtime_checkable
class StepFunc(Protocol):
    target_fixtures: list[str]


def _execute_scenario(feature: Feature, scenario: Scenario, request):
    """Execute the scenario.

    :param feature: Feature.
    :param scenario: Scenario.
    :param request: request.
    :param encoding: Encoding.
    """
    request.config.hook.pytest_bdd_before_scenario(request=request, feature=feature, scenario=scenario)

    try:
        for step in scenario.steps:
            Step.Executor(request=request, scenario=scenario, step=step).execute()
    finally:
        request.config.hook.pytest_bdd_after_scenario(request=request, feature=feature, scenario=scenario)


FakeRequest = collections.namedtuple("FakeRequest", ["module"])


def _are_examples_and_fixtures_joinable(request, bdd_example, examples_fixtures_mapping):
    joinable = True
    if bdd_example and examples_fixtures_mapping:
        for param, fixture_name in examples_fixtures_mapping.items():
            try:
                if str(request.getfixturevalue(fixture_name)) != bdd_example[param]:
                    joinable = False
                    break
            except (FixtureLookupError, KeyError):
                continue
    return joinable


def _get_scenario_decorator(
    feature: Feature,
    feature_name: str,
    templated_scenario: ScenarioTemplate,
    scenario_name: str,
    examples_fixtures_mapping: set[str] | dict[str, str] | None = None,
):
    _examples_fixtures_mapping = DefaultMapping.instantiate_from_collection_or_bool(examples_fixtures_mapping or ())
    if _examples_fixtures_mapping:
        warn(PytestDeprecationWarning("Outlining by fixtures could be removed in future versions"))

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

        external_join_keys: set[str]
        scenario_wrapper: TestFunc
        if isinstance(_examples_fixtures_mapping, dict):
            external_join_keys = set(_examples_fixtures_mapping.keys())
        elif _examples_fixtures_mapping is None:
            external_join_keys = set()
        else:
            external_join_keys = _examples_fixtures_mapping
        templated_scenario.validate(external_join_keys=external_join_keys)

        # We need to tell pytest that the original function requires its fixtures,
        # otherwise indirect fixtures would not work.
        @pytest.mark.usefixtures(*fn_args)  # type: ignore[no-redef]
        def scenario_wrapper(request: FixtureRequest, bdd_example: ExampleRowUnited) -> Any:

            _examples_fixtures_mapping.warm_up(*bdd_example.keys())
            if not _are_examples_and_fixtures_joinable(request, bdd_example, _examples_fixtures_mapping):
                pytest.skip(f"Examples and fixtures were not joined for example {bdd_example.breadcrumb}")

            scenario = templated_scenario.render(
                {
                    **{
                        param: request.getfixturevalue(fixture_name)
                        for param, fixture_name in _examples_fixtures_mapping.items()
                    },
                    **bdd_example,
                }
            )

            _execute_scenario(feature, scenario, request)
            fixture_values = [request.getfixturevalue(arg) for arg in fn_args]
            return fn(*fixture_values)

        example_parametrizations = collect_example_parametrizations(templated_scenario)
        if example_parametrizations:
            # Parametrize the scenario outlines
            scenario_wrapper = pytest.mark.parametrize("bdd_example", example_parametrizations)(scenario_wrapper)

        for tag in templated_scenario.tags.union(feature.tags):
            config = CONFIG_STACK[-1]
            # TODO deprecated usage
            if not config.hook.pytest_bdd_apply_tag(tag=tag, function=scenario_wrapper):
                apply_tag(scenario=templated_scenario, tag=tag, function=scenario_wrapper)

        scenario_wrapper.__doc__ = f"{feature_name}: {scenario_name}"
        scenario_wrapper.__scenario__ = templated_scenario
        return cast("TestFunc", scenario_wrapper)

    return decorator


def collect_example_parametrizations(
    templated_scenario: ScenarioTemplate,
) -> list[ParameterSet] | None:
    parametrizations = []
    config = CONFIG_STACK[-1]
    for united_example_row in templated_scenario.united_example_rows:

        def marks():
            for tag in united_example_row.tags:
                _marks = config.hook.pytest_bdd_convert_tag_to_marks(
                    feature=templated_scenario.feature,
                    scenario=templated_scenario,
                    example=united_example_row,
                    tag=tag,
                )
                if _marks:
                    yield from iter(_marks)

        parametrizations.append(
            pytest.param(
                united_example_row,
                id=united_example_row.breadcrumb + ":" + "-".join(united_example_row.values()),
                marks=list(marks()),
            )
        )
    return parametrizations


def scenario(
    feature_name: str,
    scenario_name: str,
    encoding: str = "utf-8",
    features_base_dir: str | None = None,
    examples_fixtures_mapping: set[str] | dict[str, str] | None = None,
):
    """Scenario decorator.

    :param feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param scenario_name: Scenario name.
    :param encoding: Feature file encoding.
    :param examples_fixtures_mapping: Mapping of examples parameter names to fixtures
    """

    scenario_name = str(scenario_name)
    caller_module_path = get_caller_module_path()

    # Get the feature
    if features_base_dir is None:
        features_base_dir = get_features_base_dir(caller_module_path)
    feature = get_feature(features_base_dir, feature_name, encoding=encoding)

    # Get the scenario
    try:
        scenario = feature.scenarios[scenario_name]
    except KeyError:
        feature_name = feature.name or "[Empty]"
        raise exceptions.ScenarioNotFound(
            f'Scenario "{scenario_name}" in feature "{feature_name}" in {feature.filename} is not found.'
        )

    return _get_scenario_decorator(
        feature=feature,
        feature_name=feature_name,
        templated_scenario=scenario,
        scenario_name=scenario_name,
        examples_fixtures_mapping=examples_fixtures_mapping,
    )


def get_features_base_dir(caller_module_path: str) -> str:
    default_base_dir = os.path.dirname(caller_module_path)
    return get_from_ini("bdd_features_base_dir", default_base_dir)


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


def scenarios(*feature_paths: str, **kwargs: Any) -> None:
    """Parse features from the paths and put all found scenarios in the caller module.

    :param *feature_paths: feature file paths to use for scenarios
    """
    caller_locals = get_caller_module_locals()
    caller_path = get_caller_module_path()

    features_base_dir = kwargs.get("features_base_dir")
    if features_base_dir is None:
        features_base_dir = get_features_base_dir(caller_path)

    abs_feature_paths = []
    for path in feature_paths:
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(features_base_dir, path))
        abs_feature_paths.append(path)
    found = False

    module_scenarios = frozenset(
        (attr.__scenario__.feature.filename, attr.__scenario__.name)
        for name, attr in caller_locals.items()
        if hasattr(attr, "__scenario__")
    )

    for feature in get_features(abs_feature_paths):
        for scenario_name, scenario_object in feature.scenarios.items():
            # skip already bound scenarios
            if (scenario_object.feature.filename, scenario_name) not in module_scenarios:

                @scenario(feature.filename, scenario_name, **kwargs)
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
