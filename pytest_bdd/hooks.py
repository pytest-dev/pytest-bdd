from __future__ import annotations

from typing import Iterable

from pytest import hookspec

from pytest_bdd.typing.pytest import Mark

"""Pytest-bdd pytest hooks."""


def pytest_bdd_before_scenario(request, feature, scenario):
    """Called before scenario is executed."""


def pytest_bdd_run_scenario(request, feature, scenario):
    """Execution scenario protocol"""


def pytest_bdd_after_scenario(request, feature, scenario):
    """Called after scenario is executed."""


def pytest_bdd_run_step(request, feature, scenario, step, previous_step):
    """Execution of run step protocol"""


def pytest_bdd_before_step(request, feature, scenario, step, step_func):
    """Called before step function is set up."""


def pytest_bdd_before_step_call(request, feature, scenario, step, step_func, step_func_args, step_definition):
    """Called before step function is executed."""


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args, step_definition):
    """Called after step function is successfully executed."""


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception, step_definition):
    """Called when step function failed to execute."""


def pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception):
    """Called when step lookup failed."""


@hookspec(firstresult=True)
def pytest_bdd_convert_tag_to_marks(feature, scenario, tag) -> Iterable[Mark] | None:
    """Apply a tag (from a ``.feature`` file) to the given test item.

    The default implementation does the equivalent of
    ``getattr(pytest.mark, tag)(function)``, but you can override this hook and
    return ``True`` to do more sophisticated handling of tags.
    """


@hookspec(firstresult=True)
def pytest_bdd_match_step_definition_to_step(request, feature, scenario, step, previous_step):
    """Find match between scenario step and user defined step function"""


@hookspec(firstresult=True)
def pytest_bdd_get_step_caller(request, feature, scenario, step, step_func, step_func_args, step_definition):
    """Provide alternative approach to execute step"""
