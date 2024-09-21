from __future__ import annotations

from collections.abc import Callable

import pytest
from _pytest.fixtures import FixtureRequest

from pytest_bdd.parser import Feature, Scenario, Step

"""Pytest-bdd pytest hooks."""


def pytest_bdd_before_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario) -> object:
    """Called before scenario is executed."""


def pytest_bdd_after_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario) -> object:
    """Called after scenario is executed."""


def pytest_bdd_before_step(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, step_func: Callable[..., object]
) -> object:
    """Called before step function is set up."""


def pytest_bdd_before_step_call(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., object],
    step_func_args: dict[str, object],
) -> object:
    """Called before step function is executed."""


def pytest_bdd_after_step(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., object],
    step_func_args: dict[str, object],
) -> object:
    """Called after step function is successfully executed."""


def pytest_bdd_step_error(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., object],
    step_func_args: dict[str, object],
    exception: Exception,
) -> object:
    """Called when step function failed to execute."""


def pytest_bdd_step_func_lookup_error(
    request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, exception: Exception
) -> object:
    """Called when step lookup failed."""


@pytest.hookspec(firstresult=True)
def pytest_bdd_apply_tag(tag: str, function: Callable[..., object]) -> object:
    """Apply a tag (from a ``.feature`` file) to the given scenario.

    The default implementation does the equivalent of
    ``getattr(pytest.mark, tag)(function)``, but you can override this hook and
    return ``True`` to do more sophisticated handling of tags.
    """
