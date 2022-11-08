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

import contextlib
import logging
import os
import re
from typing import TYPE_CHECKING, Callable, Iterator, cast

import pytest
from _pytest.fixtures import FixtureDef, FixtureManager, FixtureRequest, call_fixture_func
from _pytest.nodes import iterparentnodeids

from . import exceptions
from .feature import get_feature, get_features
from .steps import StepFunctionContext, get_step_fixture_name, inject_fixture
from .utils import CONFIG_STACK, get_args, get_caller_module_locals, get_caller_module_path

if TYPE_CHECKING:
    from typing import Any, Iterable

    from _pytest.mark.structures import ParameterSet

    from .parser import Feature, Scenario, ScenarioTemplate, Step


logger = logging.getLogger(__name__)


PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")


def find_fixturedefs_for_step(step: Step, fixturemanager: FixtureManager, nodeid: str) -> Iterable[FixtureDef[Any]]:
    """Find the fixture defs that can parse a step."""
    # happens to be that _arg2fixturedefs is changed during the iteration so we use a copy
    fixture_def_by_name = list(fixturemanager._arg2fixturedefs.items())
    for i, (fixturename, fixturedefs) in enumerate(fixture_def_by_name):
        for pos, fixturedef in enumerate(fixturedefs):
            step_func_context = getattr(fixturedef.func, "_pytest_bdd_step_context", None)
            if step_func_context is None:
                continue

            if step_func_context.type is not None and step_func_context.type != step.type:
                continue

            match = step_func_context.parser.is_matching(step.name)
            if not match:
                continue

            if fixturedef not in (fixturemanager.getfixturedefs(fixturename, nodeid) or []):
                continue

            yield fixturedef


@contextlib.contextmanager
def inject_fixturedefs_for_step(step: Step, fixturemanager: FixtureManager, nodeid: str) -> Iterator[None]:
    """Inject fixture definitions that can parse a step.

    We fist iterate over all the fixturedefs that can parse the step.

    Then we sort them by their "path" (list of parent IDs) so that we respect the fixture scoping rules.

    Finally, we inject them into the request.
    """
    bdd_name = get_step_fixture_name(step=step)

    fixturedefs = list(find_fixturedefs_for_step(step=step, fixturemanager=fixturemanager, nodeid=nodeid))

    # Sort the fixture definitions by their "path", so that the `bdd_name` fixture will
    # respect the fixture scope

    def get_fixture_path(fixture_def: FixtureDef) -> list[str]:
        return list(iterparentnodeids(fixture_def.baseid))

    fixturedefs.sort(key=lambda x: get_fixture_path(x))

    if not fixturedefs:
        yield
        return

    logger.debug("Adding providers for fixture %r: %r", bdd_name, fixturedefs)
    fixturemanager._arg2fixturedefs[bdd_name] = fixturedefs

    try:
        yield
    finally:
        del fixturemanager._arg2fixturedefs[bdd_name]


def get_step_function(request, step: Step) -> StepFunctionContext | None:
    """Get the step function (context) for the given step.

    We first figure out what's the step fixture name that we have to inject.

    Then we let `patch_argumented_step_functions` find out what step definition fixtures can parse the current step,
    and it will inject them for the step fixture name.

    Finally we let request.getfixturevalue(...) fetch the step definition fixture.
    """
    __tracebackhide__ = True
    bdd_name = get_step_fixture_name(step=step)

    with inject_fixturedefs_for_step(step=step, fixturemanager=request._fixturemanager, nodeid=request.node.nodeid):
        try:
            return cast(StepFunctionContext, request.getfixturevalue(bdd_name))
        except pytest.FixtureLookupError:
            return None


def _execute_step_function(
    request: FixtureRequest, scenario: Scenario, step: Step, context: StepFunctionContext
) -> None:
    """Execute step function."""
    __tracebackhide__ = True
    kw = {
        "request": request,
        "feature": scenario.feature,
        "scenario": scenario,
        "step": step,
        "step_func": context.step_func,
        "step_func_args": {},
    }

    request.config.hook.pytest_bdd_before_step(**kw)

    # Get the step argument values.
    converters = context.converters
    kwargs = {}
    args = get_args(context.step_func)

    try:
        parsed_args = context.parser.parse_arguments(step.name)
        assert parsed_args is not None, (
            f"Unexpected `NoneType` returned from " f"parse_arguments(...) in parser: {context.parser!r}"
        )
        for arg, value in parsed_args.items():
            if arg in converters:
                value = converters[arg](value)
            kwargs[arg] = value

        kwargs = {arg: kwargs[arg] if arg in kwargs else request.getfixturevalue(arg) for arg in args}
        kw["step_func_args"] = kwargs

        request.config.hook.pytest_bdd_before_step_call(**kw)
        # Execute the step as if it was a pytest fixture, so that we can allow "yield" statements in it
        return_value = call_fixture_func(fixturefunc=context.step_func, request=request, kwargs=kwargs)
    except Exception as exception:
        request.config.hook.pytest_bdd_step_error(exception=exception, **kw)
        raise

    if context.target_fixture is not None:
        inject_fixture(request, context.target_fixture, return_value)

    request.config.hook.pytest_bdd_after_step(**kw)


def _execute_scenario(feature: Feature, scenario: Scenario, request: FixtureRequest) -> None:
    """Execute the scenario.

    :param feature: Feature.
    :param scenario: Scenario.
    :param request: request.
    :param encoding: Encoding.
    """
    __tracebackhide__ = True
    request.config.hook.pytest_bdd_before_scenario(request=request, feature=feature, scenario=scenario)

    try:
        for step in scenario.steps:
            step_func_context = get_step_function(request=request, step=step)
            if step_func_context is None:
                exc = exceptions.StepDefinitionNotFoundError(
                    f"Step definition is not found: {step}. "
                    f'Line {step.line_number} in scenario "{scenario.name}" in the feature "{scenario.feature.filename}"'
                )
                request.config.hook.pytest_bdd_step_func_lookup_error(
                    request=request, feature=feature, scenario=scenario, step=step, exception=exc
                )
                raise exc
            _execute_step_function(request, scenario, step, step_func_context)
    finally:
        request.config.hook.pytest_bdd_after_scenario(request=request, feature=feature, scenario=scenario)


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
            __tracebackhide__ = True
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
    __tracebackhide__ = True
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
    d = get_from_ini("bdd_features_base_dir", None)
    if d is None:
        return os.path.dirname(caller_module_path)
    rootdir = CONFIG_STACK[-1].rootpath
    return os.path.join(rootdir, d)


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
