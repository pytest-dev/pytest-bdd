import pytest
from _pytest.fixtures import FixtureRequest

from pytest_bdd.model import Feature, Scenario, Step

"""Pytest-bdd pytest hooks."""


def pytest_bdd_before_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario):
    """Called before scenario is executed."""


def pytest_bdd_after_scenario(request: FixtureRequest, feature: Feature, scenario):
    """Called after scenario is executed."""


def pytest_bdd_before_step(request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, step_func):
    """Called before step function is set up."""


def pytest_bdd_before_step_call(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, step_func, step_func_args
):
    """Called before step function is executed."""


def pytest_bdd_after_step(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, step_func, step_func_args
):
    """Called after step function is successfully executed."""


def pytest_bdd_step_error(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func,
    step_func_args,
    exception: Exception,
):
    """Called when step function failed to execute."""


def pytest_bdd_step_validation_error(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func,
    step_func_args,
    exception: Exception,
):
    """Called when step failed to validate."""


def pytest_bdd_step_func_lookup_error(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, exception: Exception
):
    """Called when step lookup failed."""


@pytest.hookspec(firstresult=True)
def pytest_bdd_apply_tag(tag, function):
    """Apply a tag (from a ``.feature`` file) to the given scenario.

    The default implementation does the equivalent of
    ``getattr(pytest.mark, tag)(function)``, but you can override this hook and
    return ``True`` to do more sophisticated handling of tags.
    """
