"""Scenario implementation.

The pytest will collect the test case and the steps will be executed
line by line.

Example:

test_publish_article = scenario(
    feature_name='publish_article.feature',
    scenario_name='Publishing the article',
)

"""
import inspect  # pragma: no cover
from os import path as op  # pragma: no cover

from _pytest import python

from pytest_bdd.feature import Feature, force_encode  # pragma: no cover
from pytest_bdd.steps import recreate_function, get_caller_module, get_caller_function
from pytest_bdd.types import GIVEN


class ScenarioValidationError(Exception):
    """Base class for scenario validation."""


class ScenarioNotFound(ScenarioValidationError):  # pragma: no cover
    """Scenario Not Found"""


class NotEnoughScenarioParams(ScenarioValidationError):  # pragma: no cover
    """Scenario function doesn't take enough parameters in the arguments."""


class StepTypeError(ScenarioValidationError):  # pragma: no cover
    """Step definition is not of the type expected in the scenario."""


class GivenAlreadyUsed(ScenarioValidationError):  # pragma: no cover
    """Fixture that implements the Given has been already used."""


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
                    for arg, value in match.groupdict().items():
                        fd = python.FixtureDef(
                            request._fixturemanager,
                            fixturedef.baseid,
                            arg,
                            lambda: value, fixturedef.scope, fixturedef.params,
                            fixturedef.unittest,
                        )
                        fd.cached_result = (value, 0)

                        old_fd = getattr(request, '_fixturedefs', {}).get(arg)
                        old_value = request._funcargs.get(arg)

                        def fin():
                            request._fixturemanager._arg2fixturedefs[arg].remove(fd)
                            getattr(request, '_fixturedefs', {})[arg] = old_fd
                            request._funcargs[arg] = old_value

                        request.addfinalizer(fin)

                        # inject fixture definition
                        request._fixturemanager._arg2fixturedefs.setdefault(arg, []).insert(0, fd)
                        # inject fixture value in request cache
                        getattr(request, '_fixturedefs', {})[arg] = fd
                        request._funcargs[arg] = value
                    return request.getfuncargvalue(pattern.pattern)
        raise


def scenario(feature_name, scenario_name, encoding='utf-8'):
    """Scenario. May be called both as decorator and as just normal function."""

    caller_module = get_caller_module()
    caller_function = get_caller_function()

    def decorator(request):

        def _scenario(request):
            # Get the feature
            base_path = request.getfuncargvalue('pytestbdd_feature_base_dir')
            feature_path = op.abspath(op.join(base_path, feature_name))
            feature = Feature.get_feature(feature_path, encoding=encoding)

            # Get the scenario
            try:
                scenario = feature.scenarios[scenario_name]
            except KeyError:
                raise ScenarioNotFound(
                    'Scenario "{0}" in feature "{1}" is not found.'.format(scenario_name, feature_name)
                )

            resolved_params = scenario.params.intersection(request.fixturenames)

            if scenario.params != resolved_params:
                raise NotEnoughScenarioParams(
                    """Scenario "{0}" in the feature "{1}" was not able to resolve all declared parameters."""
                    """Should resolve params: {2}, but resolved only: {3}.""".format(
                        scenario_name, feature_name, sorted(scenario.params), sorted(resolved_params),
                    )
                )

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

                kwargs = {}
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

        _scenario.pytestbdd_params = set()

        if isinstance(request, python.FixtureRequest):
            # Called as a normal function.
            _scenario = recreate_function(_scenario, module=caller_module)
            return _scenario(request)

        # Used as a decorator. Modify the returned function to add parameters from a decorated function.
        func_args = inspect.getargspec(request).args
        if 'request' in func_args:
            func_args.remove('request')
        _scenario = recreate_function(_scenario, name=request.__name__, add_args=func_args, module=caller_module)
        _scenario.pytestbdd_params = set(func_args)

        return _scenario

    decorator = recreate_function(decorator, module=caller_module, firstlineno=caller_function.f_lineno)

    return decorator
