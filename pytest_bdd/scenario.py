"""Scenario implementation.

The pytest will collect the test case and the steps will be executed
line by line.

Example:

test_publish_article = scenario(
    feature_name='publish_article.feature',
    scenario_name='Publishing the article',
)

"""
import collections
import os
import imp

import sys
import inspect  # pragma: no cover
from os import path as op  # pragma: no cover

import pytest

from future import utils as future_utils

from _pytest import python

from pytest_bdd.feature import Feature, force_encode  # pragma: no cover
from pytest_bdd.steps import recreate_function, get_caller_module, get_caller_function
from pytest_bdd.types import GIVEN

from pytest_bdd import plugin


class ScenarioValidationError(Exception):
    """Base class for scenario validation."""


class ScenarioNotFound(ScenarioValidationError):  # pragma: no cover
    """Scenario Not Found"""


class ScenarioExamplesNotValidError(ScenarioValidationError):  # pragma: no cover
    """Scenario steps argumets do not match declared scenario examples."""


class StepTypeError(ScenarioValidationError):  # pragma: no cover
    """Step definition is not of the type expected in the scenario."""


class GivenAlreadyUsed(ScenarioValidationError):  # pragma: no cover
    """Fixture that implements the Given has been already used."""


def _inject_fixture(request, arg, value):
    """Inject fixture into pytest fixture request.

    :param request: pytest fixture request
    :param arg: argument name
    :param value: argument value

    """
    fd = python.FixtureDef(
        request._fixturemanager,
        None,
        arg,
        lambda: value, None, None,
        False,
    )
    fd.cached_result = (value, 0)

    old_fd = getattr(request, '_fixturedefs', {}).get(arg)
    old_value = request._funcargs.get(arg)
    add_fixturename = arg not in request.fixturenames

    def fin():
        request._fixturemanager._arg2fixturedefs[arg].remove(fd)
        getattr(request, '_fixturedefs', {})[arg] = old_fd
        request._funcargs[arg] = old_value
        if add_fixturename:
            request.fixturenames.remove(arg)

    request.addfinalizer(fin)

    # inject fixture definition
    request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)
    # inject fixture value in request cache
    getattr(request, '_fixturedefs', {})[arg] = fd
    request._funcargs[arg] = value
    if add_fixturename:
        request.fixturenames.append(arg)


def _find_step_function(request, name, encoding):
    """Match the step defined by the regular expression pattern.

    :param request: PyTest request object.
    :param name: Step name.

    :return: Step function.

    """

    try:
        return request.getfuncargvalue(force_encode(name, encoding))
    except python.FixtureLookupError:

        for fixturename, fixturedefs in request._fixturemanager._arg2fixturedefs.items():
            for fixturedef in fixturedefs:

                pattern = getattr(fixturedef.func, 'pattern', None)
                match = pattern.match(name) if pattern else None

                if match:
                    converters = getattr(fixturedef.func, 'converters', {})
                    for arg, value in match.groupdict().items():
                        if arg in converters:
                            value = converters[arg](value)
                        _inject_fixture(request, arg, value)
                    return request.getfuncargvalue(pattern.pattern)
        raise


def _validate_scenario(feature, scenario, request):
    """Validate the scenario."""
    if scenario.params and scenario.example_params and scenario.params != set(scenario.example_params):
        raise ScenarioExamplesNotValidError(
            """Scenario "{0}" in the feature "{1}" has not valid examples. """
            """Set of step parameters {2} should match set of example values {3}.""".format(
                scenario.name, feature.filename, sorted(scenario.params), sorted(scenario.example_params),
            )
        )


def _execute_scenario_outline(feature, scenario, request, encoding, example_converters=None):
    """Execute the scenario outline."""
    errors = []
    # tricky part, basically here we clear pytest request cache
    for example in scenario.examples:
        request._funcargs = {}
        request._arg2index = {}
        try:
            _execute_scenario(feature, scenario, request, encoding, example=dict(zip(scenario.example_params, example)))
        except Exception as e:
            errors.append([e, sys.exc_info()[2]])
    for error in errors:
        raise future_utils.raise_with_traceback(error[0], error[1])


def _execute_step_function(request, feature, step, step_func, example=None):
    """Execute step function."""
    kwargs = {}
    if example:
        for key in step.params:
            value = example[key]
            if step_func.converters and key in step_func.converters:
                value = step_func.converters[key](value)
            _inject_fixture(request, key, value)
    try:
        # Get the step argument values
        kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(step_func).args)
        request.config.hook.pytest_bdd_before_step(
            request=request, feature=feature, scenario=scenario, step=step, step_func=step_func,
            step_func_args=kwargs)
        # Execute the step
        step_func(**kwargs)
        request.config.hook.pytest_bdd_after_step(
            request=request, feature=feature, scenario=scenario, step=step, step_func=step_func,
            step_func_args=kwargs)
    except Exception as exception:
        request.config.hook.pytest_bdd_step_error(
            request=request, feature=feature, scenario=scenario, step=step, step_func=step_func,
            step_func_args=kwargs, exception=exception)
        raise


def _execute_scenario(feature, scenario, request, encoding, example=None):
    """Execute the scenario."""

    _validate_scenario(feature, scenario, request)

    givens = set()
    # Execute scenario steps
    for step in scenario.steps:
        try:
            step_func = _find_step_function(request, step.name, encoding=encoding)
        except python.FixtureLookupError as exception:
            request.config.hook.pytest_bdd_step_func_lookup_error(
                request=request, feature=feature, scenario=scenario, step=step, exception=exception)
            raise

        try:
            # Check the step types are called in the correct order
            if step_func.step_type != step.type:
                raise StepTypeError(
                    'Wrong step type "{0}" while "{1}" is expected.'.format(step_func.step_type, step.type)
                )

            # Check if the fixture that implements given step has not been yet used by another given step
            if step.type == GIVEN:
                if step_func.fixture in givens:
                    raise GivenAlreadyUsed(
                        'Fixture "{0}" that implements this "{1}" given step has been already used.'.format(
                            step_func.fixture, step.name,
                        )
                    )
                givens.add(step_func.fixture)
        except ScenarioValidationError as exception:
            request.config.hook.pytest_bdd_step_validation_error(
                request=request, feature=feature, scenario=scenario, step=step, step_func=step_func,
                exception=exception)
            raise

        _execute_step_function(request, feature, step, step_func, example=example)


FakeRequest = collections.namedtuple('FakeRequest', ['module'])


def get_fixture(caller_module, fixture, path=None, module=None):
    """Get first conftest module from given one."""
    def call_fixture(function):
        args = []
        if 'request' in inspect.getargspec(function).args:
            args = [FakeRequest(module=caller_module)]
        return function(*args)

    if not module:
        module = caller_module

    if hasattr(module, fixture):
        return call_fixture(getattr(module, fixture))

    if path is None:
        path = os.path.dirname(module.__file__)
    if os.path.exists(os.path.join(path, '__init__.py')):
        file_path = os.path.join(path, 'conftest.py')
        if os.path.exists(file_path):
            conftest = imp.load_source('conftest', file_path)
            if hasattr(conftest, fixture):
                return get_fixture(caller_module, fixture, module=conftest)
    else:
        return get_fixture(caller_module, fixture, module=plugin)
    return get_fixture(caller_module, fixture, path=os.path.dirname(path), module=module)


def scenario(
        feature_name, scenario_name, encoding='utf-8', example_converters=None,
        caller_module=None, caller_function=None):
    """Scenario."""

    caller_module = caller_module or get_caller_module()
    caller_function = caller_function or get_caller_function()

    # Get the feature
    base_path = get_fixture(caller_module, 'pytestbdd_feature_base_dir')
    feature_path = op.abspath(op.join(base_path, feature_name))
    feature = Feature.get_feature(feature_path, encoding=encoding)

    # Get the scenario
    try:
        scenario = feature.scenarios[scenario_name]
    except KeyError:
        raise ScenarioNotFound(
            'Scenario "{0}" in feature "{1}" is not found.'.format(scenario_name, feature_name)
        )

    if scenario.examples:
        params = []
        for example in scenario.examples:
            for index, param in enumerate(scenario.example_params):
                if example_converters and param in example_converters:
                    example[index] = example_converters[param](example[index])
            params.append(example)
        params = [scenario.example_params, params]
    else:
        params = []

    def _scenario(request, *args, **kwargs):
        _execute_scenario(feature, scenario, request, encoding)

    _scenario = recreate_function(
        _scenario, module=caller_module, firstlineno=caller_function.f_lineno,
        add_args=scenario.example_params)
    if params:
        _scenario = pytest.mark.parametrize(*params)(_scenario)
    return _scenario
