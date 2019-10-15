% if features:
# coding=utf-8
"""${ features[0].name or features[0].rel_filename } feature tests."""

from pytest_bdd import (
    given,
    scenario,
    then,
    when,
)


% endif
% for scenario in sorted(scenarios, key=lambda scenario: scenario.name):
@scenario('${scenario.feature.rel_filename}', ${ repr(scenario.name)})
def test_${ make_python_name(scenario.name)}():
    ${make_python_docstring(scenario.name)}


% endfor
% for step in steps:
@${step.type}(${ repr(step.name)})
def ${ make_python_name(step.name)}():
    ${make_python_docstring(step.name)}
    raise NotImplementedError
% if not loop.last:


% endif
% endfor
