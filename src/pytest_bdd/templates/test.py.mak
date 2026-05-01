% if features:
"""${ features[0].name or features[0].rel_filename } feature tests."""

from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)


% endif
% for feature in dict.fromkeys(scenario.feature for scenario in scenarios):
scenarios(${ make_string_literal(feature.rel_filename.replace("\\", "/"))})


% endfor
% for step in steps:
@${step.type}(${ make_string_literal(step.name)})
def _():
    ${make_python_docstring(step.name)}
    raise NotImplementedError
% if not loop.last:


% endif
% endfor
