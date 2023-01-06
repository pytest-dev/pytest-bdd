% if features:
"""${ features[0].name or features[0].rel_filename } feature tests."""

from pathlib import Path

from pytest_bdd import (
    scenario,
    given,
    when,
    then,
    step,
)


% endif
% for feature, pickle in feature_pickles :
@scenario(Path('${feature.rel_filename}'), ${ make_string_literal(pickle.name)})
def test_${ make_python_name(pickle.name)}():
    ${make_python_docstring(pickle.name)}


% endfor
% for feature_pickle, step in feature_pickle_steps:
@${step_type_to_method_name[step.type]}(${ make_string_literal(step.text)})
def ${ make_python_name(step.text)}():
    ${make_python_docstring(step.text)}
    raise NotImplementedError
% if not loop.last:


% endif
% endfor
