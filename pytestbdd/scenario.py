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

from pytestbdd.library import Library
from pytestbdd.feature import Feature


def scenario(feature_name, scenario_name):
    """Scenario."""
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    feature_path = op.abspath(op.join(op.dirname(module.__file__), feature_name))

    def _scenario(request):
        library = Library(request, module)
        feature = Feature.get_feature(feature_path)
        scenario = feature.scenarios[scenario_name]

        # Evaluate given steps (can have side effects)
        for given in scenario.given:
            fixture = library.given[given]
            request.getfuncargvalue(fixture)

        # Execute when steps
        for when in scenario.when:
            _execute_step(request, library.when[when])

        # Assert then steps
        for then in scenario.then:
            result = _execute_step(request, library.then[then])
            assert result or result is None

    return _scenario


def _execute_step(request, func):
    """Execute the step.

    :param request: pytest request object.
    :param func: Step Python function.

    :note: Steps can take pytest fixture parameters. They will be evaluated
    from the request and passed to the step function.
    """
    kwargs = dict((arg, request.getfuncargvalue(arg)) for arg in inspect.getargspec(func).args)
    return func(**kwargs)
