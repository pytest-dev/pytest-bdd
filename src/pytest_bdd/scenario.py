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
from collections.abc import Iterable, Iterator
from inspect import signature
from typing import TYPE_CHECKING, Callable, TypeVar, cast
from weakref import WeakKeyDictionary

import pytest
from _pytest.fixtures import FixtureDef, FixtureManager, FixtureRequest, call_fixture_func

from . import exceptions
from .compat import getfixturedefs, inject_fixture
from .feature import get_feature, get_features
from .steps import StepFunctionContext, get_step_fixture_name, step_function_context_registry
from .utils import (
    CONFIG_STACK,
    get_caller_module_locals,
    get_caller_module_path,
    get_required_args,
    identity,
    registry_get_safe,
)

if TYPE_CHECKING:
    from _pytest.mark.structures import ParameterSet
    from _pytest.nodes import Node

    from .parser import Feature, Scenario, ScenarioTemplate, Step

T = TypeVar("T")

logger = logging.getLogger(__name__)

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")

STEP_ARGUMENT_DATATABLE = "datatable"
STEP_ARGUMENT_DOCSTRING = "docstring"
STEP_ARGUMENTS_RESERVED_NAMES = {STEP_ARGUMENT_DATATABLE, STEP_ARGUMENT_DOCSTRING}

scenario_wrapper_template_registry: WeakKeyDictionary[Callable[..., object], ScenarioTemplate] = WeakKeyDictionary()


def find_fixturedefs_for_step(step: Step, fixturemanager: FixtureManager, node: Node) -> Iterable[FixtureDef[object]]:
    """Find the fixture defs that can parse a step."""
    # happens to be that _arg2fixturedefs is changed during the iteration so we use a copy
    fixture_def_by_name = list(fixturemanager._arg2fixturedefs.items())
    for fixturename, fixturedefs in fixture_def_by_name:
        for _, fixturedef in enumerate(fixturedefs):
            step_func_context = step_function_context_registry.get(fixturedef.func)
            if step_func_context is None:
                continue

            if step_func_context.type is not None and step_func_context.type != step.type:
                continue

            match = step_func_context.parser.is_matching(step.name)
            if not match:
                continue

            fixturedefs = list(getfixturedefs(fixturemanager, fixturename, node) or [])
            if fixturedef not in fixturedefs:
                continue

            yield fixturedef


# Function copied from pytest 8.0 (removed in later versions).
def iterparentnodeids(nodeid: str) -> Iterator[str]:
    """Return the parent node IDs of a given node ID, inclusive.

    For the node ID

        "testing/code/test_excinfo.py::TestFormattedExcinfo::test_repr_source"

    the result would be

        ""
        "testing"
        "testing/code"
        "testing/code/test_excinfo.py"
        "testing/code/test_excinfo.py::TestFormattedExcinfo"
        "testing/code/test_excinfo.py::TestFormattedExcinfo::test_repr_source"

    Note that / components are only considered until the first ::.
    """
    SEP = "/"
    pos = 0
    first_colons: int | None = nodeid.find("::")
    if first_colons == -1:
        first_colons = None
    # The root Session node - always present.
    yield ""
    # Eagerly consume SEP parts until first colons.
    while True:
        at = nodeid.find(SEP, pos, first_colons)
        if at == -1:
            break
        if at > 0:
            yield nodeid[:at]
        pos = at + len(SEP)
    # Eagerly consume :: parts.
    while True:
        at = nodeid.find("::", pos)
        if at == -1:
            break
        if at > 0:
            yield nodeid[:at]
        pos = at + len("::")
    # The node ID itself.
    if nodeid:
        yield nodeid


@contextlib.contextmanager
def inject_fixturedefs_for_step(step: Step, fixturemanager: FixtureManager, node: Node) -> Iterator[None]:
    """Inject fixture definitions that can parse a step.

    We fist iterate over all the fixturedefs that can parse the step.

    Then we sort them by their "path" (list of parent IDs) so that we respect the fixture scoping rules.

    Finally, we inject them into the request.
    """
    bdd_name = get_step_fixture_name(step=step)

    fixturedefs = list(find_fixturedefs_for_step(step=step, fixturemanager=fixturemanager, node=node))

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


def get_step_function(request: FixtureRequest, step: Step) -> StepFunctionContext | None:
    """Get the step function (context) for the given step.

    We first figure out what's the step fixture name that we have to inject.

    Then we let `patch_argumented_step_functions` find out what step definition fixtures can parse the current step,
    and it will inject them for the step fixture name.

    Finally, we let request.getfixturevalue(...) fetch the step definition fixture.
    """
    __tracebackhide__ = True
    bdd_name = get_step_fixture_name(step=step)

    with inject_fixturedefs_for_step(step=step, fixturemanager=request._fixturemanager, node=request.node):
        try:
            return cast(StepFunctionContext, request.getfixturevalue(bdd_name))
        except pytest.FixtureLookupError:
            return None


def parse_step_arguments(step: Step, context: StepFunctionContext) -> dict[str, object]:
    """Parse step arguments."""
    parsed_args = context.parser.parse_arguments(step.name)

    assert (
        parsed_args is not None
    ), f"Unexpected `NoneType` returned from parse_arguments(...) in parser: {context.parser!r}"

    reserved_args = set(parsed_args.keys()) & STEP_ARGUMENTS_RESERVED_NAMES
    if reserved_args:
        reserved_arguments_str = ", ".join(repr(arg) for arg in reserved_args)
        raise exceptions.StepImplementationError(
            f"Step {step.name!r} defines argument names that are reserved: {reserved_arguments_str}. "
            "Please use different names."
        )

    converted_args = {key: (context.converters.get(key, identity)(value)) for key, value in parsed_args.items()}

    return converted_args


def _execute_step_function(
    request: FixtureRequest, scenario: Scenario, step: Step, context: StepFunctionContext
) -> None:
    """Execute step function."""
    __tracebackhide__ = True

    func_sig = signature(context.step_func)

    kw = {
        "request": request,
        "feature": scenario.feature,
        "scenario": scenario,
        "step": step,
        "step_func": context.step_func,
        "step_func_args": {},
    }
    request.config.hook.pytest_bdd_before_step(**kw)

    try:
        parsed_args = parse_step_arguments(step=step, context=context)

        # Filter out the arguments that are not in the function signature
        kwargs = {k: v for k, v in parsed_args.items() if k in func_sig.parameters}

        if STEP_ARGUMENT_DATATABLE in func_sig.parameters and step.datatable is not None:
            kwargs[STEP_ARGUMENT_DATATABLE] = step.datatable.raw()
        if STEP_ARGUMENT_DOCSTRING in func_sig.parameters and step.docstring is not None:
            kwargs[STEP_ARGUMENT_DOCSTRING] = step.docstring

        # Fill the missing arguments requesting the fixture values
        kwargs |= {
            arg: request.getfixturevalue(arg) for arg in get_required_args(context.step_func) if arg not in kwargs
        }

        kw["step_func_args"] = kwargs

        request.config.hook.pytest_bdd_before_step_call(**kw)

        # Execute the step as if it was a pytest fixture using `call_fixture_func`,
        # so that we can allow "yield" statements in it
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
) -> Callable[[Callable[..., T]], Callable[[FixtureRequest, dict[str, str]], T]]:
    # HACK: Ideally we would use `def decorator(fn)`, but we want to return a custom exception
    # when the decorator is misused.
    # Pytest inspect the signature to determine the required fixtures, and in that case it would look
    # for a fixture called "fn" that doesn't exist (if it exists then it's even worse).
    # It will error with a "fixture 'fn' not found" message instead.
    # We can avoid this hack by using a pytest hook and check for misuse instead.
    def decorator(*args: Callable[..., T]) -> Callable[[FixtureRequest, dict[str, str]], T]:
        if not args:
            raise exceptions.ScenarioIsDecoratorOnly(
                "scenario function can only be used as a decorator. Refer to the documentation."
            )
        [fn] = args
        func_args = get_required_args(fn)

        def scenario_wrapper(request: FixtureRequest, _pytest_bdd_example: dict[str, str]) -> T:
            __tracebackhide__ = True
            scenario = templated_scenario.render(_pytest_bdd_example)
            _execute_scenario(feature, scenario, request)
            fixture_values = [request.getfixturevalue(arg) for arg in func_args]
            return fn(*fixture_values)

        if func_args:
            # We need to tell pytest that the original function requires its fixtures,
            # otherwise indirect fixtures would not work.
            scenario_wrapper = pytest.mark.usefixtures(*func_args)(scenario_wrapper)

        example_parametrizations = collect_example_parametrizations(templated_scenario)
        if example_parametrizations is not None:
            # Parametrize the scenario outlines
            scenario_wrapper = pytest.mark.parametrize(
                "_pytest_bdd_example",
                example_parametrizations,
            )(scenario_wrapper)

        rule_tags = set() if templated_scenario.rule is None else templated_scenario.rule.tags
        for tag in templated_scenario.tags | feature.tags | rule_tags:
            config = CONFIG_STACK[-1]
            config.hook.pytest_bdd_apply_tag(tag=tag, function=scenario_wrapper)

        scenario_wrapper.__doc__ = f"{feature_name}: {scenario_name}"

        scenario_wrapper_template_registry[scenario_wrapper] = templated_scenario
        return scenario_wrapper

    return decorator


def collect_example_parametrizations(
    templated_scenario: ScenarioTemplate,
) -> list[ParameterSet] | None:
    parametrizations = []

    for examples in templated_scenario.examples:
        tags: set = examples.tags or set()

        example_marks = [getattr(pytest.mark, tag) for tag in tags]

        for context in examples.as_contexts():
            param_id = "-".join(context.values())
            parametrizations.append(
                pytest.param(
                    context,
                    id=param_id,
                    marks=example_marks,
                ),
            )

    return parametrizations or None


def scenario(
    feature_name: str,
    scenario_name: str,
    encoding: str = "utf-8",
    features_base_dir: str | None = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Scenario decorator.

    :param str feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param str scenario_name: Scenario name.
    :param str encoding: Feature file encoding.
    :param features_base_dir: Optional base dir location for locating feature files. If not set, it will try and resolve using property set in .ini file, then the caller_module_path.
    """
    __tracebackhide__ = True
    scenario_name = scenario_name
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
        ) from None

    return _get_scenario_decorator(
        feature=feature, feature_name=feature_name, templated_scenario=scenario, scenario_name=scenario_name
    )


def get_features_base_dir(caller_module_path: str) -> str:
    d = get_from_ini("bdd_features_base_dir")
    if d is None:
        return os.path.dirname(caller_module_path)
    rootdir = CONFIG_STACK[-1].rootpath
    return os.path.join(rootdir, d)


def get_from_ini(key: str, default: str | None = None) -> str | None:
    """Get value from ini config. Return default if value has not been set.

    Use if the default value is dynamic. Otherwise, set default on addini call.
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


def scenarios(*feature_paths: str, encoding: str = "utf-8", features_base_dir: str | None = None) -> None:
    caller_locals = get_caller_module_locals()
    """Parse features from the paths and put all found scenarios in the caller module.

    :param *feature_paths: feature file paths to use for scenarios
    :param str encoding: Feature file encoding.
    :param features_base_dir: Optional base dir location for locating feature files. If not set, it will try and
      resolve using property set in .ini file, otherwise it is assumed to be relative from the caller path location.
    """
    caller_path = get_caller_module_path()

    if features_base_dir is None:
        features_base_dir = get_features_base_dir(caller_path)

    abs_feature_paths = []
    for path in feature_paths:
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(features_base_dir, path))
        abs_feature_paths.append(path)
    found = False

    module_scenarios = frozenset(
        (s.feature.filename, s.name)
        for name, attr in caller_locals.items()
        if (s := registry_get_safe(scenario_wrapper_template_registry, attr)) is not None
    )

    for feature in get_features(abs_feature_paths):
        for scenario_name, scenario_object in feature.scenarios.items():
            # skip already bound scenarios
            if (scenario_object.feature.filename, scenario_name) not in module_scenarios:

                @scenario(feature.filename, scenario_name, encoding=encoding, features_base_dir=features_base_dir)
                def _scenario() -> None:
                    pass  # pragma: no cover

                for test_name in get_python_name_generator(scenario_name):
                    if test_name not in caller_locals:
                        # found a unique test name
                        caller_locals[test_name] = _scenario
                        break
            found = True
    if not found:
        raise exceptions.NoScenariosFound(abs_feature_paths)
