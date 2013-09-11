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

from pytest_bdd.feature import Feature  # pragma: no cover
from pytest_bdd.steps import recreate_function


class ScenarioNotFound(Exception):  # pragma: no cover
    """Scenario Not Found"""


class NotEnoughScenarioParams(Exception):  # pragma: no cover
    pass


def scenario(feature_name=None, scenario_name=None):
    """Scenario. May be called both as decorator and as just normal function."""

    def decorator(request):

        def _scenario(request):

            # Determine the feature_name and scenario_name
            if not scenario_name and not feature_name:
                raise Exception("No parameters given; there's nothing we can do.")

            if not scenario_name:
                try:
                    scenarioname = feature_name
                    featurename = request.getfuncargvalue('pytestbdd_feature_file')
                except python.FixtureLookupError:
                    raise Exception("Feature file path was not found. " +
                                    "Specify the pytestbdd_feature_file fixture, " +
                                    "or send the feature_name as first argument or kwarg.")
            else:
                scenarioname = scenario_name
                featurename = feature_name

            # Get the feature file
            base_path = request.getfuncargvalue('pytestbdd_feature_base_dir')
            feature_path = op.abspath(op.join(base_path, featurename))
            feature = Feature.get_feature(feature_path)

            # Get the scenario
            try:
                scenario = feature.scenarios[scenarioname]
            except KeyError:
                raise ScenarioNotFound(
                    'Scenario "{0}" in feature "{1}" is not found.'.format(scenarioname, featurename))

            resolved_params = scenario.params.intersection(request.fixturenames)

            if scenario.params != resolved_params:
                raise NotEnoughScenarioParams(
                    """Scenario "{0}" in the feature "{1}" was not able to resolve all declared parameters."""
                    """Should resolve params: {2}, but resolved only: {3}.""".format(
                    scenarioname, featurename, sorted(scenario.params), sorted(resolved_params)))

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
