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
from typing import TYPE_CHECKING, Callable, cast

import pytest
from _pytest.fixtures import FixtureLookupError, FixtureManager, FixtureRequest, call_fixture_func

from . import exceptions
from .feature import get_feature, get_features
from .steps import get_step_fixture_name, inject_fixture
from .utils import CONFIG_STACK, get_args, get_caller_module_locals, get_caller_module_path

if TYPE_CHECKING:
    from typing import Any, Iterable

    from _pytest.mark.structures import ParameterSet

    from .parser import Feature, Scenario, ScenarioTemplate, Step

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")


def find_argumented_step_fixture_name(
    name: str, type_: str, fixturemanager: FixtureManager, request: FixtureRequest | None = None
) -> str | None:
    """Find argumented step fixture name."""
    # happens to be that _arg2fixturedefs is changed during the iteration so we use a copy
    for fixturename, fixturedefs in list(fixturemanager._arg2fixturedefs.items()):
        for fixturedef in fixturedefs:
            parsers = getattr(fixturedef.func, "_pytest_bdd_parsers", [])
            for parser in parsers:
                match = parser.is_matching(name)
                if not match:
                    continue

                parser_name = get_step_fixture_name(parser.name, type_)
                if request:
                    try:
                        request.getfixturevalue(parser_name)
                    except FixtureLookupError:
                        continue
                return parser_name
    return None


def _find_step_function(request: FixtureRequest, step: Step, scenario: Scenario) -> Any:
    """Match the step defined by the regular expression pattern.

    :param request: PyTest request object.
    :param step: Step.
    :param scenario: Scenario.

    :return: Function of the step.
    :rtype: function
    """
    name = step.name
    try:
        # Simple case where no parser is used for the step
        return request.getfixturevalue(get_step_fixture_name(name, step.type))
    except FixtureLookupError as e:
        try:
            # Could not find a fixture with the same name, let's see if there is a parser involved
            argumented_name = find_argumented_step_fixture_name(name, step.type, request._fixturemanager, request)
            if argumented_name:
                return request.getfixturevalue(argumented_name)
            raise e
        except FixtureLookupError as e2:
            raise exceptions.StepDefinitionNotFoundError(
                f"Step definition is not found: {step}. "
                f'Line {step.line_number} in scenario "{scenario.name}" in the feature "{scenario.feature.filename}"'
            ) from e2


def _execute_step_function(request: FixtureRequest, scenario: Scenario, step: Step, step_func: Callable) -> None:
    """Execute step function.

    :param request: PyTest request.
    :param scenario: Scenario.
    :param step: Step.
    :param function step_func: Step function.
    :param example: Example table.
    """
    kw = dict(request=request, feature=scenario.feature, scenario=scenario, step=step, step_func=step_func)

    request.config.hook.pytest_bdd_before_step(**kw)

    kw["step_func_args"] = {}
    try:
        # Get the step argument values.
        converters = getattr(step_func, "converters", {})
        kwargs = {}

        parsers = getattr(step_func, "_pytest_bdd_parsers", [])

        for parser in parsers:
            if not parser.is_matching(step.name):
                continue
            for arg, value in parser.parse_arguments(step.name).items():
                if arg in converters:
                    value = converters[arg](value)
                kwargs[arg] = value
            break

        kwargs = {arg: kwargs[arg] if arg in kwargs else request.getfixturevalue(arg) for arg in get_args(step_func)}
        kw["step_func_args"] = kwargs

        request.config.hook.pytest_bdd_before_step_call(**kw)
        target_fixture = getattr(step_func, "target_fixture", None)

        # Execute the step as if it was a pytest fixture, so that we can allow "yield" statements in it
        return_value = call_fixture_func(fixturefunc=step_func, request=request, kwargs=kwargs)
        if target_fixture:
            inject_fixture(request, target_fixture, return_value)

        request.config.hook.pytest_bdd_after_step(**kw)
    except Exception as exception:
        request.config.hook.pytest_bdd_step_error(exception=exception, **kw)
        raise


def _execute_scenario(feature: Feature, scenario: Scenario, request: FixtureRequest) -> None:
    """Execute the scenario.

    :param feature: Feature.
    :param scenario: Scenario.
    :param request: request.
    :param encoding: Encoding.
    """
    request.config.hook.pytest_bdd_before_scenario(request=request, feature=feature, scenario=scenario)

    try:
        # Execute scenario steps
        for step in scenario.steps:
            try:
                step_func = _find_step_function(request, step, scenario)
            except exceptions.StepDefinitionNotFoundError as exception:
                request.config.hook.pytest_bdd_step_func_lookup_error(
                    request=request, feature=feature, scenario=scenario, step=step, exception=exception
                )
                raise
            _execute_step_function(request, scenario, step, step_func)
    finally:
        request.config.hook.pytest_bdd_after_scenario(request=request, feature=feature, scenario=scenario)


FakeRequest = collections.namedtuple("FakeRequest", ["module"])


def _get_scenario_decorator(
    feature: Feature, feature_name: str, templated_scenario: ScenarioTemplate, scenario_name: str
) -> Callable[[Callable], Callable]:
    # HACK: Ideally we would use `def decorator(fn)`, but we want to return a custom exception
    # when the decorator is misused.
    # Pytest inspect the signature to determine the required fixtures, and in that case it would look
    # for a fixture called "fn" that doesn't exist (if it exists then it's even worse).
    # It will error with a "fixture 'fn' not found" message instead.
    # We can avoid this hack by using a pytest hook and check for misuse instead.
    def decorator(*args: Callable) -> Callable:
        if not args:
            raise exceptions.ScenarioIsDecoratorOnly(
                "scenario function can only be used as a decorator. Refer to the documentation."
            )
        [fn] = args
        func_args = get_args(fn)

        # We need to tell pytest that the original function requires its fixtures,
        # otherwise indirect fixtures would not work.
        @pytest.mark.usefixtures(*func_args)
        def scenario_wrapper(request: FixtureRequest, _pytest_bdd_example: dict[str, str]) -> Any:
            scenario = templated_scenario.render(_pytest_bdd_example)
            _execute_scenario(feature, scenario, request)
            fixture_values = [request.getfixturevalue(arg) for arg in func_args]
            return fn(*fixture_values)

        example_parametrizations = collect_example_parametrizations(templated_scenario)
        if example_parametrizations is not None:
            # Parametrize the scenario outlines
            scenario_wrapper = pytest.mark.parametrize(
                "_pytest_bdd_example",
                example_parametrizations,
            )(scenario_wrapper)

        for tag in templated_scenario.tags.union(feature.tags):
            config = CONFIG_STACK[-1]
            config.hook.pytest_bdd_apply_tag(tag=tag, function=scenario_wrapper)

        scenario_wrapper.__doc__ = f"{feature_name}: {scenario_name}"
        scenario_wrapper.__scenario__ = templated_scenario
        return cast(Callable, scenario_wrapper)

    return decorator


def collect_example_parametrizations(
    templated_scenario: ScenarioTemplate,
) -> list[ParameterSet] | None:
    # We need to evaluate these iterators and store them as lists, otherwise
    # we won't be able to do the cartesian product later (the second iterator will be consumed)
    contexts = list(templated_scenario.examples.as_contexts())
    if not contexts:
        return None

    return [pytest.param(context, id="-".join(context.values())) for context in contexts]


def scenario(
    feature_name: str, scenario_name: str, encoding: str = "utf-8", features_base_dir=None
) -> Callable[[Callable], Callable]:
    """Scenario decorator.

    :param str feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param str scenario_name: Scenario name.
    :param str encoding: Feature file encoding.
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
        feature=feature, feature_name=feature_name, templated_scenario=scenario, scenario_name=scenario_name
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
