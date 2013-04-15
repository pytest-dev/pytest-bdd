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

from pytest_bdd.types import THEN
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
            # Evaluate the fixture, also applies to given
            func = request.getfuncargvalue(step)
            if getattr(func, '__step_type__', None) is None:
                continue

            # Execute when and then steps
            kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(func).args)
            result = func(**kwargs)
            if func.__step_type__ == THEN:
                assert result is None or result

    return _scenario
