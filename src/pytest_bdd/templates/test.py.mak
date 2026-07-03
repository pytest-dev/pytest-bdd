<%
    feature_paths = sorted(set(f.rel_filename for f in features))
%>\
% if features:
"""${ features[0].name or features[0].rel_filename } feature tests."""

from pytest_bdd import (
    given,
    scenarios,
    then,
    when,
)

% for feature_path in feature_paths:
scenarios('${feature_path}')
% endfor


% endif
% for step in steps:
@${step.type}(${ make_string_literal(step.name)})
def _():
    ${make_python_docstring(step.name)}
    raise NotImplementedError
% if not loop.last:


% endif
% endfor
