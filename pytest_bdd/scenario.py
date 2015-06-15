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
import re

import pytest
from _pytest import python
import six

from . import exceptions
from . import fixtures
from .feature import (
    Feature,
    force_encode,
    force_unicode,
    get_features,
)
from .steps import (
    execute,
    get_caller_function,
    get_caller_module,
    get_step_fixture_name,
    inject_fixture,
    recreate_function,
)
from .types import GIVEN

if six.PY3:
    import runpy

    def execfile(filename, init_globals):
        """Execute given file as a python script in given globals environment."""
        result = runpy.run_path(filename, init_globals=init_globals)
        init_globals.update(result)


PYTHON_REPLACE_REGEX = re.compile("\W")
ALPHA_REGEX = re.compile("^\d+_*")


def find_argumented_step_fixture_name(name, type_, fixturemanager, request=None):
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
                        inject_fixture(request, arg, value)
                parser_name = get_step_fixture_name(parser.name, type_)
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
        return request.getfuncargvalue(get_step_fixture_name(name, step.type, encoding))
    except python.FixtureLookupError:
        try:
            name = find_argumented_step_fixture_name(name, step.type, request._fixturemanager, request)
            if name:
                return request.getfuncargvalue(name)
            raise
        except python.FixtureLookupError:
            raise exceptions.StepDefinitionNotFoundError(
                u"""Step definition is not found: {step}."""
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
    kw = dict(
        request=request,
        feature=scenario.feature,
        scenario=scenario,
        step=step,
        step_func=step_func,
    )

    request.config.hook.pytest_bdd_before_step(**kw)

    if example:
        for key in step.params:
            value = example[key]
            if step_func.converters and key in step_func.converters:
                value = step_func.converters[key](value)
            inject_fixture(request, key, value)

    kw["step_func_args"] = {}
    try:
        # Get the step argument values.
        kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(step_func).args)
        kw["step_func_args"] = kwargs

        request.config.hook.pytest_bdd_before_step_call(**kw)
        # Execute the step.
        step_func(**kwargs)
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
        return call_fixture(getattr(fixtures, fixture))
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

        code = """def {name}({function_args}):
            _execute_scenario(feature, scenario, request, encoding)
            _pytestbdd_function({args})""".format(
            name=_pytestbdd_function.__name__,
            function_args=", ".join(function_args),
            args=", ".join(args))

        execute(code, g)

        _scenario = recreate_function(
            g[_pytestbdd_function.__name__],
            module=caller_module,
            firstlineno=caller_function.f_lineno,
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
        return _scenario

    return recreate_function(decorator, module=caller_module, firstlineno=caller_function.f_lineno)


def scenario(feature_name, scenario_name, encoding="utf-8", example_converters=None,
             caller_module=None, caller_function=None):
    """Scenario decorator.

    :param str feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param str scenario_name: Scenario name.
    :param str encoding: Feature file encoding.
    :param dict example_converters: optional `dict` of example converter function, where key is the name of the
        example parameter, and value is the converter function.
    """
    scenario_name = force_unicode(scenario_name, encoding)
    caller_module = caller_module or get_caller_module()
    caller_function = caller_function or get_caller_function()

    # Get the feature
    base_path = get_fixture(caller_module, "pytestbdd_feature_base_dir")
    strict_gherkin = get_fixture(caller_module, "pytestbdd_strict_gherkin")
    feature = Feature.get_feature(base_path, feature_name, encoding=encoding, strict_gherkin=strict_gherkin)

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


def make_python_name(string):
    """Make python attribute name out of a given string."""
    string = re.sub(PYTHON_REPLACE_REGEX, "", string.replace(" ", "_"))
    return re.sub(ALPHA_REGEX, "", string).lower()


def get_python_name_generator(name):
    """Generate a sequence of suitable python names out of given arbitrary string name."""
    python_name = make_python_name(name)
    suffix = ''
    index = 0

    def get_name():
        return 'test_{0}{1}'.format(python_name, suffix)
    while True:
        yield get_name()
        index += 1
        suffix = '_{0}'.format(index)


def scenarios(*feature_paths, **kwargs):
    """Parse features from the paths and put all found scenarios in the caller module.

    :param *feature_paths: feature file paths to use for scenarios
    """
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    base_path = get_fixture(module, "pytestbdd_feature_base_dir")
    abs_feature_paths = []
    for path in feature_paths:
        if not os.path.isabs(path):
            path = os.path.abspath(os.path.join(base_path, path))
        abs_feature_paths.append(path)
    found = False

    module_scenarios = frozenset(
        (attr.__scenario__.feature.filename, attr.__scenario__.name)
        for name, attr in module.__dict__.items() if hasattr(attr, '__scenario__'))
    for feature in get_features(abs_feature_paths):
        for scenario_name, scenario_object in feature.scenarios.items():
            # skip already bound scenarios
            if (scenario_object.feature.filename, scenario_name) not in module_scenarios:
                @scenario(feature.filename, scenario_name, **kwargs)
                def _scenario():
                    pass
                for test_name in get_python_name_generator(scenario_name):
                    if test_name not in module.__dict__:
                        # found an unique test name
                        module.__dict__[test_name] = _scenario
                        break
            found = True
    if not found:
        raise exceptions.NoScenariosFound(abs_feature_paths)
