"""Pytest-bdd pytest hooks."""


def pytest_bdd_step_func_lookup(request, feature, scenario, step):
    """Called before step function is lookep up."""


def pytest_bdd_step_func_found(request, feature, scenario, step, step_func):
    """Called when step function is found."""


def pytest_bdd_step_start(request, feature, scenario, step, step_func, step_func_args):
    """Called before step function is executed."""


def pytest_bdd_step_finish(request, feature, scenario, step, step_func, step_func_args):
    """Called after step function is successfully executed."""


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Called when step function failed to execute."""


def pytest_bdd_step_validation_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Called when step failed to validate."""


def pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception):
    """Called when step failed to validate."""
