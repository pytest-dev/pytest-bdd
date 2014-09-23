% if features:
"""${ features[0].name or features[0].rel_filename } feature tests."""
from functools import partial

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


% endif
% for scenario in sorted(scenarios, key=lambda scenario: scenario.name):
@scenario('${scenario.feature.rel_filename}', '${scenario.name}')
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
