"""pytest-bdd Exceptions."""


class ScenarioIsDecoratorOnly(Exception):
    """Scenario can be only used as decorator."""


class ScenarioValidationError(Exception):
    """Base class for scenario validation."""


class ScenarioNotFound(ScenarioValidationError):
    """Scenario Not Found"""


class ScenarioExamplesNotValidError(ScenarioValidationError):
    """Scenario steps argumets do not match declared scenario examples."""


class StepTypeError(ScenarioValidationError):
    """Step definition is not of the type expected in the scenario."""


class GivenAlreadyUsed(ScenarioValidationError):
    """Fixture that implements the Given has been already used."""


class StepDefinitionNotFoundError(Exception):
    """Step definition not found."""
