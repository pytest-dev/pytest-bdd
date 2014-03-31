"""pytest-bdd Exceptions."""


class ScenarioIsDecoratorOnly(Exception):
    """Scenario can be only used as decorator."""


class ScenarioValidationError(Exception):
    """Base class for scenario validation."""


class ScenarioNotFound(ScenarioValidationError):  # pragma: no cover
    """Scenario Not Found"""


class ScenarioExamplesNotValidError(ScenarioValidationError):  # pragma: no cover
    """Scenario steps argumets do not match declared scenario examples."""


class StepTypeError(ScenarioValidationError):  # pragma: no cover
    """Step definition is not of the type expected in the scenario."""


class GivenAlreadyUsed(ScenarioValidationError):  # pragma: no cover
    """Fixture that implements the Given has been already used."""


class StepDefinitionNotFoundError(Exception):  # pragma: no cover
    """Step definition not found."""
