from __future__ import annotations

import linecache
import re
import textwrap
import typing
from dataclasses import dataclass, field
from typing import Any

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner

from . import exceptions

if typing.TYPE_CHECKING:
    from typing_extensions import Self


ERROR_PATTERNS = [
    (
        re.compile(r"expected:.*got 'Feature.*'"),
        exceptions.FeatureError,
        "Multiple features are not allowed in a single feature file.",
    ),
    (
        re.compile(r"expected:.*got '(?:Given|When|Then|And|But).*'"),
        exceptions.FeatureError,
        "Step definition outside of a Scenario or a Background.",
    ),
    (
        re.compile(r"expected:.*got 'Background.*'"),
        exceptions.BackgroundError,
        "Multiple 'Background' sections detected. Only one 'Background' is allowed per feature.",
    ),
    (
        re.compile(r"expected:.*got 'Scenario Outline.*'"),
        exceptions.ScenarioOutlineError,
        "'Scenario Outline' requires steps before 'Examples'.",
    ),
    (
        re.compile(r"expected:.*got 'Scenario.*'"),
        exceptions.ScenarioError,
        "Misplaced or incorrect 'Scenario' keyword. Ensure it's correctly placed.",
    ),
    (
        re.compile(r"expected:.*got 'Examples.*'"),
        exceptions.ExamplesError,
        "'Examples' must follow a valid 'Scenario Outline' and contain table rows.",
    ),
    (
        re.compile(r"expected:.*got 'Given.*'"),
        exceptions.StepError,
        "Improper step keyword detected. Ensure correct order and indentation for steps (Given, When, Then, etc.).",
    ),
    (
        re.compile(r"expected:.*got 'TagLine.*'"),
        exceptions.TagError,
        "Tags are misplaced. They should be directly above features, scenarios, or outlines.",
    ),
    (
        re.compile(r"expected:.*got 'Rule.*'"),
        exceptions.RuleError,
        "Misplaced or incorrectly formatted 'Rule'. Ensure it follows the feature structure.",
    ),
    (
        re.compile(r"expected:.*got 'DocString.*'"),
        exceptions.DocStringError,
        'DocString must be enclosed in triple quotes ("""). Ensure proper formatting.',
    ),
    (
        re.compile(r"expected:.*got '.*'"),
        exceptions.TokenError,
        "Unexpected token found. Check Gherkin syntax near the reported error.",
    ),
]


@dataclass
class Location:
    column: int
    line: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(column=data["column"], line=data["line"])


@dataclass
class Comment:
    location: Location
    text: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(location=Location.from_dict(data["location"]), text=data["text"])


@dataclass
class Cell:
    location: Location
    value: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(location=Location.from_dict(data["location"]), value=_to_raw_string(data["value"]))


@dataclass
class Row:
    id: str
    location: Location
    cells: list[Cell]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            location=Location.from_dict(data["location"]),
            cells=[Cell.from_dict(cell) for cell in data["cells"]],
        )


@dataclass
class DataTable:
    location: Location
    name: str | None = None
    tableHeader: Row | None = None
    tableBody: list[Row] | None = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            location=Location.from_dict(data["location"]),
            name=data.get("name"),
            tableHeader=Row.from_dict(data["tableHeader"]) if data.get("tableHeader") else None,
            tableBody=[Row.from_dict(row) for row in data.get("tableBody", [])],
        )


@dataclass
class DocString:
    content: str
    delimiter: str
    location: Location

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            content=textwrap.dedent(data["content"]),
            delimiter=data["delimiter"],
            location=Location.from_dict(data["location"]),
        )


@dataclass
class Step:
    id: str
    keyword: str
    keywordType: str
    location: Location
    text: str
    dataTable: DataTable | None = None
    docString: DocString | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            keyword=data["keyword"].strip(),
            keywordType=data["keywordType"],
            location=Location.from_dict(data["location"]),
            text=data["text"],
            dataTable=DataTable.from_dict(data["dataTable"]) if data.get("dataTable") else None,
            docString=DocString.from_dict(data["docString"]) if data.get("docString") else None,
        )


@dataclass
class Tag:
    id: str
    location: Location
    name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(id=data["id"], location=Location.from_dict(data["location"]), name=data["name"])


@dataclass
class Scenario:
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    steps: list[Step]
    tags: list[Tag]
    examples: list[DataTable] | None = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            name=data["name"],
            description=data["description"],
            steps=[Step.from_dict(step) for step in data["steps"]],
            tags=[Tag.from_dict(tag) for tag in data["tags"]],
            examples=[DataTable.from_dict(example) for example in data.get("examples", [])],
        )


@dataclass
class Rule:
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    tags: list[Tag]
    children: list[Child]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            name=data["name"],
            description=data["description"],
            tags=[Tag.from_dict(tag) for tag in data["tags"]],
            children=[Child.from_dict(child) for child in data["children"]],
        )


@dataclass
class Background:
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    steps: list[Step]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            name=data["name"],
            description=data["description"],
            steps=[Step.from_dict(step) for step in data["steps"]],
        )


@dataclass
class Child:
    background: Background | None = None
    rule: Rule | None = None
    scenario: Scenario | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            background=Background.from_dict(data["background"]) if data.get("background") else None,
            rule=Rule.from_dict(data["rule"]) if data.get("rule") else None,
            scenario=Scenario.from_dict(data["scenario"]) if data.get("scenario") else None,
        )


@dataclass
class Feature:
    keyword: str
    location: Location
    tags: list[Tag]
    name: str
    description: str
    children: list[Child]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            tags=[Tag.from_dict(tag) for tag in data["tags"]],
            name=data["name"],
            description=data["description"],
            children=[Child.from_dict(child) for child in data["children"]],
        )


@dataclass
class GherkinDocument:
    feature: Feature
    comments: list[Comment]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            feature=Feature.from_dict(data["feature"]),
            comments=[Comment.from_dict(comment) for comment in data["comments"]],
        )


def _to_raw_string(normal_string: str) -> str:
    return normal_string.replace("\\", "\\\\")


def get_gherkin_document(abs_filename: str, encoding: str = "utf-8") -> GherkinDocument:
    with open(abs_filename, encoding=encoding) as f:
        feature_file_text = f.read()

    try:
        gherkin_data = Parser().parse(TokenScanner(feature_file_text))
    except CompositeParserException as e:
        message = e.args[0]
        line = e.errors[0].location["line"]
        line_content = linecache.getline(abs_filename, e.errors[0].location["line"]).rstrip("\n")
        filename = abs_filename
        gherkin_error_handler = GherkinParserErrorHandler()
        gherkin_error_handler(message, line, line_content, filename)
        # If no patterns matched, raise a generic GherkinParserError
        raise exceptions.GherkinParseError(f"Unknown parsing error: {message}", line, line_content, filename)

    # At this point, the `gherkin_data` should be valid if no exception was raised
    return GherkinDocument.from_dict(gherkin_data)


class GherkinParserErrorHandler:
    """Parses raw Gherkin parser errors and converts them to human-readable exceptions."""

    def __call__(self, raw_error: str, line: int, line_content: str, filename: str):
        """Map the error message to a specific exception type and raise it."""
        # Split the raw_error into individual lines
        error_lines = raw_error.splitlines()

        # Check each line against all error patterns
        for error_line in error_lines:
            for pattern, exception_class, message in ERROR_PATTERNS:
                if pattern.search(error_line):
                    # If a match is found, raise the corresponding exception with the formatted message
                    raise exception_class(message, line, line_content, filename)
