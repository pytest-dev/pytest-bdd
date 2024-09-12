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


class GherkinParseError(Exception):
    """Base class for all Gherkin parsing errors."""

    def __init__(self, message, line, line_content, filename):
        super().__init__(message)
        self.message = message
        self.line = line
        self.line_content = line_content
        self.filename = filename
        self.line = line
        self.line_content = line_content
        self.filename = filename

    def __str__(self):
        return f"{self.__class__.__name__}: {self.message}\nLine number: {self.line}\nLine: {self.line_content}\nFile: {self.filename}"


class FeatureError(GherkinParseError):
    pass


class BackgroundError(GherkinParseError):
    pass


class ScenarioOutlineError(GherkinParseError):
    pass


class ScenarioError(GherkinParseError):
    pass


class ExamplesError(GherkinParseError):
    pass


class StepError(GherkinParseError):
    pass


class TagError(GherkinParseError):
    pass


class RuleError(GherkinParseError):
    pass


class DocStringError(GherkinParseError):
    pass


class TokenError(GherkinParseError):
    pass
