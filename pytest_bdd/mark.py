"""Pytest-bdd markers."""
import inspect

from pytest_bdd.steps import recreate_function, get_caller_module, get_caller_function

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

        _scenario = recreate_function(_scenario, name=request.__name__, module=caller_module, add_args=args)

        return _scenario

    return recreate_function(decorator, module=caller_module, firstlineno=caller_function.f_lineno)
