# TODO: Delete this file
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import TypeAlias

    TableType: TypeAlias = list[tuple[str, ...]]


class GherkinSyntaxError(Exception):
    label = "Gherkin syntax error"

    def __init__(self, context: str, line: int, column: int | None = None, filename: str | None = None):
        self.context = context
        self.line = line
        self.column = column
        self.filename = filename

    def __str__(self):
        filename = self.filename if self.filename is not None else "<unknown>"
        message = f"{self.label} at line {self.line}"
        if self.column is not None:
            message += f", column {self.column}"
        message += f":\n\n{self.context}\n\nFile: {filename}"
        return message


class GherkinMultipleFeatures(GherkinSyntaxError):
    label = "Multiple features found"


class GherkinMissingFeatureDefinition(GherkinSyntaxError):
    label = "Missing feature definition"


class GherkinMissingFeatureName(GherkinSyntaxError):
    label = "Missing feature name"


class GherkinInvalidDocstring(GherkinSyntaxError):
    label = "Invalid docstring"


class GherkinUnexpectedInput(GherkinSyntaxError):
    label = "Unexpected input"


class GherkinInvalidTable(GherkinSyntaxError):
    label = "Invalid table"
