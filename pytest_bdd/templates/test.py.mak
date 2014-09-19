"""${ feature.name or feature.rel_filename } feature tests."""
from functools import partial

from pytest_bdd import (given, when, then, scenario)

scenario = partial(scenario, feature.filename)


% for scenario in sorted(scenarios, key=lambda scenario: scenario.name):
@scenario('${scenario.name}')
def test_${ make_python_name(scenario.name)}():
    """${scenario.name}."""


% endfor
% for step in steps:
@${step.type}('${step.name}')
def ${ make_python_name(step.name)}():
    """${step.name}."""
% if not loop.last:


% endif
% endfor
