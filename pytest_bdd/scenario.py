"""Scenario implementation.

The pytest will collect the test case and the steps will be executed
line by line.

Example:

test_publish_article = scenario(
    feature_name="publish_article.feature",
    scenario_name="Publishing the article",
)
"""
import collections
import inspect
import os

import pytest
from _pytest import python
import six

from . import exceptions
from . import fixtures
from .feature import (
    Feature,
    force_encode,
    force_unicode,
)
from .steps import (
    contribute_to_module,
    execute,
    get_caller_function,
    get_caller_module,
    get_function_name,
    recreate_function,
)
from .types import GIVEN


if six.PY3:
    import runpy
    execfile = runpy.run_path


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
    fd.cached_result = (value, 0, None)

    old_fd = getattr(request, "_fixturedefs", {}).get(arg)
    old_value = request._funcargs.get(arg)
    add_fixturename = arg not in request.fixturenames

    def fin():
        request._fixturemanager._arg2fixturedefs[arg].remove(fd)
        getattr(request, "_fixturedefs", {})[arg] = old_fd
        request._funcargs[arg] = old_value
        if add_fixturename:
            request.fixturenames.remove(arg)

    request.addfinalizer(fin)

    # inject fixture definition
    request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)
    # inject fixture value in request cache
    getattr(request, "_fixturedefs", {})[arg] = fd
    request._funcargs[arg] = value
    if add_fixturename:
        request.fixturenames.append(arg)


def find_argumented_step_fixture_name(name, fixturemanager, request=None):
    """Find argumented step fixture name."""
    # happens to be that _arg2fixturedefs is changed during the iteration so we use a copy
    for fixturename, fixturedefs in list(fixturemanager._arg2fixturedefs.items()):
        for fixturedef in fixturedefs:
            parser = getattr(fixturedef.func, "parser", None)
            match = parser.is_matching(name) if parser else None
            if match:
                converters = getattr(fixturedef.func, "converters", {})
                for arg, value in parser.parse_arguments(name).items():
                    if arg in converters:
                        value = converters[arg](value)
                    if request:
                        _inject_fixture(request, arg, value)
                parser_name = force_encode(parser.name)
                if request:
                    try:
                        request.getfuncargvalue(parser_name)
                    except python.FixtureLookupError:
                        continue
                return parser_name


def _find_step_function(request, step, scenario, encoding):
    """Match the step defined by the regular expression pattern.

    :param request: PyTest request object.
    :param step: Step.
    :param scenario: Scenario.

    :return: Function of the step.
    :rtype: function
    """
    name = step.name
    try:
        return request.getfuncargvalue(force_encode(name, encoding))
    except python.FixtureLookupError:
        try:
            name = find_argumented_step_fixture_name(name, request._fixturemanager, request)
            if name:
                return request.getfuncargvalue(name)
            raise
        except python.FixtureLookupError:
            raise exceptions.StepDefinitionNotFoundError(
                u"""Step definition is not found: "{step.name}"."""
                """ Line {step.line_number} in scenario "{scenario.name}" in the feature "{feature.filename}""".format(
                    step=step,
                    scenario=scenario,
                    feature=scenario.feature,
                )
            )


def _execute_step_function(request, scenario, step, step_func, example=None):
    """Execute step function.

    :param request: PyTest request.
    :param scenario: Scenario.
    :param step: Step.
    :param function step_func: Step function.
    :param example: Example table.
    """
    request.config.hook.pytest_bdd_before_step(
        request=request,
        feature=scenario.feature,
        scenario=scenario,
        step=step,
        step_func=step_func,
    )
    kwargs = {}
    if example:
        for key in step.params:
            value = example[key]
            if step_func.converters and key in step_func.converters:
                value = step_func.converters[key](value)
            _inject_fixture(request, key, value)

    kw = dict(
        request=request,
        feature=scenario.feature,
        scenario=scenario,
        step=step,
        step_func=step_func,
        step_func_args=kwargs,
    )

    try:
        # Get the step argument values.
        kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(step_func).args)

        # Execute the step.
        step_func(**kwargs)
        kw["step_func_args"] = kwargs
        request.config.hook.pytest_bdd_after_step(**kw)
    except Exception as exception:
        request.config.hook.pytest_bdd_step_error(exception=exception, **kw)
        raise


def _execute_scenario(feature, scenario, request, encoding, example=None):
    """Execute the scenario.

    :param feature: Feature.
    :param scenario: Scenario.
    :param request: request.
    :param encoding: Encoding.
    :param example: Example.
    """
    request.config.hook.pytest_bdd_before_scenario(
        request=request,
        feature=feature,
        scenario=scenario,
    )

    try:
        givens = set()
        # Execute scenario steps
        for step in scenario.steps:
            try:
                step_func = _find_step_function(request, step, scenario, encoding=encoding)
            except exceptions.StepDefinitionNotFoundError as exception:
                request.config.hook.pytest_bdd_step_func_lookup_error(
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    exception=exception,
                )
                raise

            try:
                # Check the step types are called in the correct order
                if step_func.step_type != step.type:
                    raise exceptions.StepTypeError(
                        'Wrong step type "{0}" while "{1}" is expected.'.format(step_func.step_type, step.type)
                    )

                # Check if the fixture that implements given step has not been yet used by another given step
                if step.type == GIVEN:
                    if step_func.fixture in givens:
                        raise exceptions.GivenAlreadyUsed(
                            u'Fixture "{0}" that implements this "{1}" given step has been already used.'.format(
                                step_func.fixture, step.name,
                            )
                        )
                    givens.add(step_func.fixture)
            except exceptions.ScenarioValidationError as exception:
                request.config.hook.pytest_bdd_step_validation_error(
                    request=request,
                    feature=feature,
                    scenario=scenario,
                    step=step,
                    step_func=step_func,
                    exception=exception,
                )
                raise

            _execute_step_function(request, scenario, step, step_func, example=example)
    finally:
        request.config.hook.pytest_bdd_after_scenario(
            request=request,
            feature=feature,
            scenario=scenario,
        )


FakeRequest = collections.namedtuple("FakeRequest", ["module"])


def get_fixture(caller_module, fixture, path=None):
    """Get first conftest module from given one."""
    def call_fixture(function):
        args = []
        if "request" in inspect.getargspec(function).args:
            args = [FakeRequest(module=caller_module)]
        return function(*args)

    if path is None:
        if hasattr(caller_module, fixture):
            return call_fixture(getattr(caller_module, fixture))
        path = os.path.dirname(caller_module.__file__)

    if os.path.exists(os.path.join(path, "__init__.py")):
        file_path = os.path.join(path, "conftest.py")
        if os.path.exists(file_path):
            globs = {}
            execfile(file_path, globs)
            if fixture in globs:
                return call_fixture(globs[fixture])
    else:
        return call_fixture(fixtures.pytestbdd_feature_base_dir)
    return get_fixture(caller_module, fixture, path=os.path.dirname(path))


def _get_scenario_decorator(feature, feature_name, scenario, scenario_name, caller_module, caller_function, encoding):
    """Get scenario decorator."""
    g = locals()
    g["_execute_scenario"] = _execute_scenario

    scenario_name = force_encode(scenario_name, encoding)

    def decorator(_pytestbdd_function):
        if isinstance(_pytestbdd_function, python.FixtureRequest):
            raise exceptions.ScenarioIsDecoratorOnly(
                "scenario function can only be used as a decorator. Refer to the documentation.",
            )

        g.update(locals())

        args = inspect.getargspec(_pytestbdd_function).args
        function_args = list(args)
        for arg in scenario.example_params:
            if arg not in function_args:
                function_args.append(arg)
        if "request" not in function_args:
            function_args.append("request")

        name = _pytestbdd_function.__name__

        re_contribute = not name.startswith('test_')
        name = get_function_name(scenario_name, prefix='test_') if re_contribute else name

        code = """def {name}({function_args}):
            _execute_scenario(feature, scenario, request, encoding)
            _pytestbdd_function({args})""".format(
            name=name,
            function_args=", ".join(function_args),
            args=", ".join(args))

        execute(code, g)

        _scenario = recreate_function(
            g[name],
            module=caller_module,
            firstlineno=caller_function.f_lineno,
            name=name,
        )

        params = scenario.get_params()

        if params:
            _scenario = pytest.mark.parametrize(*params)(_scenario)

        for tag in scenario.tags.union(feature.tags):
            _scenario = getattr(pytest.mark, tag)(_scenario)

        _scenario.__doc__ = "{feature_name}: {scenario_name}".format(
            feature_name=feature_name, scenario_name=scenario_name)
        _scenario.__scenario__ = scenario
        scenario.test_function = _scenario

        if re_contribute:
            contribute_to_module(caller_module, name, _scenario)
        return _scenario

    return recreate_function(
        decorator, module=caller_module, firstlineno=caller_function.f_lineno)


def scenario(feature_name, scenario_name, encoding="utf-8", example_converters=None,
             caller_module=None, caller_function=None):
    """Scenario."""
    scenario_name = force_unicode(scenario_name, encoding)
    caller_module = caller_module or get_caller_module()
    caller_function = caller_function or get_caller_function()

    # Get the feature
    base_path = get_fixture(caller_module, "pytestbdd_feature_base_dir")
    feature = Feature.get_feature(base_path, feature_name, encoding=encoding)

    # Get the sc_enario
    try:
        scenario = feature.scenarios[scenario_name]
    except KeyError:
        raise exceptions.ScenarioNotFound(
            u'Scenario "{scenario_name}" in feature "{feature_name}" in {feature_filename} is not found.'.format(
                scenario_name=scenario_name,
                feature_name=feature.name or "[Empty]",
                feature_filename=feature.filename,
            )
        )

    scenario.example_converters = example_converters

    # Validate the scenario
    scenario.validate()

    return _get_scenario_decorator(
        feature,
        feature_name,
        scenario,
        scenario_name,
        caller_module,
        caller_function,
        encoding,
    )
