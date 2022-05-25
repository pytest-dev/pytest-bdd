"""pytest-bdd public API."""
from __future__ import annotations

from pytest_bdd.packaging import get_distribution_version
from pytest_bdd.scenario import scenario, scenarios
from pytest_bdd.steps import given, step, then, when
from pytest_bdd.warning_types import (
    PytestBDDScenarioExamplesExtraParamsWarning,
    PytestBDDScenarioStepsExtraPramsWarning,
    PytestBDDStepDefinitionWarning,
)

__version__ = str(get_distribution_version("pytest-bdd-ng"))

__all__ = ["given", "when", "then", "scenario", "scenarios"]
