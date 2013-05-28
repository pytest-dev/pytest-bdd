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
        feature_path = op.abspath(op.join(op.dirname(request.module.__file__), feature_name))
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


def scenarios(feature_name):
    """Parse feature from the file and put all scenarious in caller module."""
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])

    if not op.isabs(feature_name):
        feature_path = op.abspath(op.join(op.dirname(module.__file__), feature_name))
    else:
        feature_path = feature_name

    feature = Feature.get_feature(feature_path)

    for scenario_name in feature.scenarios:
        def _scenario(request):
            # Get the scenario
            try:
                scenario = feature.scenarios[scenario_name]
            except KeyError:
                raise ScenarioNotFound(
                    'Scenario "{0}" in feature "{1}" is not found'.format(scenario_name, feature_name))

            # Execute scenario's steps
            for step in scenario.steps:
                func = request.getfuncargvalue(step)
                kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(func).args)
                func(**kwargs)

        module.__dict__['test_' + scenario_name] = _scenario

    return feature
