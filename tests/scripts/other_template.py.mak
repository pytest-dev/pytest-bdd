% if features:
"""${ features[0].name } feature tests generated with an alternative template."""
from pytest_bdd import given, then, when

from my_helpers import set_full_scenario_path


scenario = set_full_scenario_path('${features[0].rel_filename}')


% endif
% for scenario in sorted(scenarios, key=lambda scenario: scenario.name):
@scenario('${scenario.name}')
def test_${ make_python_name(scenario.name)}():
    pass


% endfor
% for step in steps:
@${step.type}('${step.name}')
def ${ make_python_name(step.name)}():
    pass
% if not loop.last:


% endif
% endfor
