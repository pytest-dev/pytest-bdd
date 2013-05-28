"""Scenario implementation.

The pytest will collect the test case and the steps will be executed
line by line.

Example:

test_publish_article = scenario(
    feature_name='publish_article.feature',
    scenario_name='Publishing the article',
)
"""
import inspect
from os import path as op

from pytest_bdd.feature import Feature


class ScenarioNotFound(Exception):
    """Scenario Not Found"""


def scenario(feature_name, scenario_name):
    """Scenario."""

    def _scenario(request):
        # Get the feature
        base_path = request.getfuncargvalue('pytestbdd_feature_base_dir')
        feature_path = op.abspath(op.join(base_path, feature_name))
        feature = Feature.get_feature(feature_path)

        # Get the scenario
        try:
            scenario = feature.scenarios[scenario_name]
        except KeyError:
            raise ScenarioNotFound('Scenario "{0}" in feature "{1}" is not found'.format(scenario_name, feature_name))

        # Execute scenario's steps
        for step in scenario.steps:
            func = request.getfuncargvalue(step)
            kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(func).args)
            func(**kwargs)

    return _scenario
