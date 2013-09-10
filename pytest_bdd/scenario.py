"""Scenario implementation.

The pytest will collect the test case and the steps will be executed
line by line.

Example:

test_publish_article = scenario(
    feature_name='publish_article.feature',
    scenario_name='Publishing the article',
)
import rpdb2
rpdb2.start_embedded_debugger('lalalala')
"""

import inspect  # pragma: no cover
from os import path as op  # pragma: no cover

from _pytest import python

from pytest_bdd.feature import Feature  # pragma: no cover
from pytest_bdd.steps import recreate_function


class ScenarioNotFound(Exception):  # pragma: no cover
    """Scenario Not Found"""


class NotEnoughScenarioParams(Exception):  # pragma: no cover
    pass


def scenario(*args):
    """Scenario. May be called both as decorator and as just normal function."""

    def decorator(request):

        def _scenario(request):

            # Determine the feature_name and scenario_name
            if len(args) > 0 and len(args) < 3:
                if '.feature' in args[0]:
                    feature_name = args[0]
                    scenario_name = args[1]
                else:
                    scenario_name = args[0]
                    try:
                        feature_name = request.module.PYTESTBDD_FEATURE_FILE
                    except:
                        raise Exception("Feature file path or name was not found. " +
                                        "Either specify the PYTESTBDD_FEATURE_FILE or send the name to this function")
            else:
                raise Exception("Call this function either with <feature_file>, <scenario_name> as arguments or with only <scenario_name>")

            # Get the feature file
            base_path = request.getfuncargvalue('pytestbdd_feature_base_dir')
            feature_path = op.abspath(op.join(base_path, feature_name))
            feature = Feature.get_feature(feature_path)


            # Get the scenario
            try:
                scenario = feature.scenarios[scenario_name]
            except KeyError:
                raise ScenarioNotFound(
                    'Scenario "{0}" in feature "{1}" is not found.'.format(scenario_name, feature_name))

            resolved_params = scenario.params.intersection(request.fixturenames)

            if scenario.params != resolved_params:
                raise NotEnoughScenarioParams(
                    """Scenario "{0}" in the feature "{1}" was not able to resolve all declared parameters."""
                    """Should resolve params: {2}, but resolved only: {3}.""".format(
                    scenario_name, feature_name, sorted(scenario.params), sorted(resolved_params)))

            # Execute scenario's steps
            for step in scenario.steps:
                step_func = request.getfuncargvalue(step)
                kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(step_func).args)
                step_func(**kwargs)

        _scenario.pytestbdd_params = set()

        if isinstance(request, python.FixtureRequest):
            # Called as a normal function.
            return _scenario(request)

        # Used as a decorator. Modify the returned function to add parameters from a decorated function.
        func_args = inspect.getargspec(request).args
        if 'request' in func_args:
            func_args.remove('request')
        _scenario = recreate_function(_scenario, name=request.__name__, add_args=func_args)
        _scenario.pytestbdd_params = set(func_args)

        return _scenario

    return decorator
