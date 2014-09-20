"""Pytest-bdd pytest hooks."""


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    """Called before step function is executed."""


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    """Called after step function is successfully executed."""


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Called when step function failed to execute."""


def pytest_bdd_step_validation_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Called when step failed to validate."""


def pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception):
    """Called when step lookup failed."""
