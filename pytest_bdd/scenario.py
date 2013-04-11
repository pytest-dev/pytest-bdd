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

from pytest_bdd.library import Library
from pytest_bdd.feature import Feature
from pytest_bdd.types import THEN


class ScenarioNotFound(Exception):
    """Scenario Not Found"""


def scenario(feature_name, scenario_name):
    """Scenario."""

    def _scenario(request):
        feature_path = op.abspath(op.join(op.dirname(request.module.__file__), feature_name))
        library = Library(request)
        feature = Feature.get_feature(feature_path)
        try:
            scenario = feature.scenarios[scenario_name]
        except KeyError:
            raise ScenarioNotFound('Scenario "{0}" in feature "{1}" is not found'.format(scenario_name, feature_name))

        # Evaluate given steps (can have side effects)
        for given in scenario.given:
            fixture = library.given[given]
            request.getfuncargvalue(fixture)

        # Execute other steps
        for step in scenario.steps:
            _execute_step(request, library.steps[step])

    return _scenario


def _execute_step(request, func):
    """Execute the step.

    :param request: pytest request object.
    :param func: Step Python function.

    :note: Steps can take pytest fixture parameters. They will be evaluated
    from the request and passed to the step function.
    """
    kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(func).args)
    result = func(**kwargs)
    if func.__step_type__ == THEN:
        assert result or result is None
