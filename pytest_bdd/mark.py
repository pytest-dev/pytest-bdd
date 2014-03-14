"""Pytest-bdd markers."""
import inspect

import pytest

from pytest_bdd.steps import execute, recreate_function, get_caller_module, get_caller_function

from pytest_bdd import scenario as bdd_scenario


def scenario(feature_name, scenario_name, encoding='utf-8', example_converters=None):
    """Scenario. May be called both as decorator and as just normal function."""

    caller_module = get_caller_module()
    caller_function = get_caller_function()

    def decorator(request):
        _scenario = bdd_scenario(
            feature_name, scenario_name, encoding=encoding, example_converters=example_converters,
            caller_module=caller_module, caller_function=caller_function)

        args = inspect.getargspec(request).args

        if 'request' not in args:
            args.insert(0, 'request')

        g = globals().copy()
        g.update(locals())

        pytestbdd_params = _scenario.pytestbdd_params
        scenario = _scenario.scenario

        sc_args = list(scenario.example_params)
        if 'request' not in sc_args:
            sc_args.insert(0, 'request')

        for arg in scenario.example_params:
            if arg not in args:
                args.append(arg)

        code = """def {name}({args}):
                _scenario({scenario_args})""".format(
            name=request.__name__,
            args=', '.join(args),
            scenario_args=', '.join(sc_args))

        execute(code, g)

        _scenario = recreate_function(g[request.__name__], module=caller_module)

        if pytestbdd_params:
            _scenario = pytest.mark.parametrize(*pytestbdd_params)(_scenario)

        return _scenario

    return recreate_function(decorator, module=caller_module, firstlineno=caller_function.f_lineno)
