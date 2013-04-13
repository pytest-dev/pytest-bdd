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
        # get feature
        feature_path = op.abspath(op.join(op.dirname(request.module.__file__), feature_name))
        feature = Feature.get_feature(feature_path)

        # get scenario
        try:
            scenario = feature.scenarios[scenario_name]
        except KeyError:
            raise ScenarioNotFound('Scenario "{0}" in feature "{1}" is not found'.format(scenario_name, feature_name))

        # execute scenario's steps
        for step in scenario.steps:
            _execute_step(request, step)

    return _scenario


def _execute_step(request, name):
    """Execute the step.

    :param request: pytest request object.
    :param name: Step name.

    :note: Steps can take pytest fixture parameters. They will be evaluated
    from the request and passed to the step function.
    """
    fixture = request.getfuncargvalue(name)

    # if fixture is a callable and has a __step_type__ then it's a step fixture
    if callable(fixture) and hasattr(fixture, '__step_type__'):
        kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(fixture).args)
        # calling an action
        fixture(**kwargs)
