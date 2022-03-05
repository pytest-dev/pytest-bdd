"""pytest-bdd Exceptions."""
from __future__ import annotations


class ScenarioIsDecoratorOnly(Exception):
    """Scenario can be only used as decorator."""


class ScenarioValidationError(Exception):
    """Base class for scenario validation."""


class ScenarioNotFound(ScenarioValidationError):
    """Scenario Not Found."""


class ExamplesNotValidError(ScenarioValidationError):
    """Example table is not valid."""


class StepDefinitionNotFoundError(Exception):
    """Step definition not found."""


class NoScenariosFound(Exception):
    """No scenarios found."""


class FeatureError(Exception):
    """Feature parse error."""

    message = "{0}.\nLine number: {1}.\nLine: {2}.\nFile: {3}"

    def __str__(self) -> str:
        """String representation."""
        return self.message.format(*self.args)
