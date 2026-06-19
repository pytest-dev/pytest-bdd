from __future__ import annotations

import linecache
import re
import textwrap
import typing
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from gherkin.dialect import Dialect  # type: ignore
from gherkin.errors import CompositeParserException  # type: ignore
from gherkin.parser import Parser  # type: ignore

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
        re.compile(r"expected:.*got 'Scenario.*'"),
        exceptions.ScenarioError,
        "Misplaced or incorrect 'Scenario' keyword. Ensure it's correctly placed. There might be a missing Feature section.",
    ),
    (
        re.compile(r"expected:.*got 'Given.*'"),
        exceptions.StepError,
        "Improper step keyword detected. Ensure correct order and indentation for steps (Given, When, Then, etc.).",
    ),
    (
        re.compile(r"expected:.*got 'Rule.*'"),
        exceptions.RuleError,
        "Misplaced or incorrectly formatted 'Rule'. Ensure it follows the feature structure.",
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
class ExamplesTable:
    location: Location
    tags: list[Tag]
    name: str | None = None
    table_header: Row | None = None
    table_body: list[Row] | None = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            location=Location.from_dict(data["location"]),
            name=data.get("name"),
            table_header=Row.from_dict(data["tableHeader"]) if data.get("tableHeader") else None,
            table_body=[Row.from_dict(row) for row in data.get("tableBody", [])],
            tags=[Tag.from_dict(tag) for tag in data["tags"]],
        )


@dataclass
class DataTable:
    location: Location
    rows: list[Row]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            location=Location.from_dict(data["location"]), rows=[Row.from_dict(row) for row in data.get("rows", [])]
        )

    def raw(self) -> Sequence[Sequence[object]]:
        return [[cell.value for cell in row.cells] for row in self.rows]


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
    location: Location
    keyword: str
    keyword_type: str
    text: str
    datatable: DataTable | None = None
    docstring: DocString | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            location=Location.from_dict(data["location"]),
            keyword=data["keyword"].strip(),
            keyword_type=data["keywordType"],
            text=data["text"],
            datatable=DataTable.from_dict(data["dataTable"]) if data.get("dataTable") else None,
            docstring=DocString.from_dict(data["docString"]) if data.get("docString") else None,
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
    location: Location
    keyword: str
    name: str
    description: str
    steps: list[Step]
    tags: list[Tag]
    examples: list[ExamplesTable] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            location=Location.from_dict(data["location"]),
            keyword=data["keyword"],
            name=data["name"],
            description=data["description"],
            steps=[Step.from_dict(step) for step in data["steps"]],
            tags=[Tag.from_dict(tag) for tag in data["tags"]],
            examples=[ExamplesTable.from_dict(example) for example in data["examples"]],
        )


@dataclass
class Rule:
    id: str
    location: Location
    keyword: str
    name: str
    description: str
    tags: list[Tag]
    children: list[Child]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            location=Location.from_dict(data["location"]),
            keyword=data["keyword"],
            name=data["name"],
            description=data["description"],
            tags=[Tag.from_dict(tag) for tag in data["tags"]],
            children=[Child.from_dict(child) for child in data["children"]],
        )


@dataclass
class Background:
    id: str
    location: Location
    keyword: str
    name: str
    description: str
    steps: list[Step]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            id=data["id"],
            location=Location.from_dict(data["location"]),
            keyword=data["keyword"],
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
    location: Location
    language: str
    keyword: str
    tags: list[Tag]
    name: str
    description: str
    children: list[Child]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        return cls(
            location=Location.from_dict(data["location"]),
            language=data["language"],
            keyword=data["keyword"],
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
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
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
        gherkin_data = Parser().parse(feature_file_text)
    except CompositeParserException as e:
        message = e.args[0]
        line = e.errors[0].location["line"]
        line_content = linecache.getline(abs_filename, e.errors[0].location["line"]).rstrip("\n")
        filename = abs_filename
        handle_gherkin_parser_error(message, line, line_content, filename, e)
        # If no patterns matched, raise a generic GherkinParserError
        raise exceptions.GherkinParseError(f"Unknown parsing error: {message}", line, line_content, filename) from e

    # At this point, the `gherkin_data` should be valid if no exception was raised
    _raise_if_step_in_feature_description(gherkin_data, feature_file_text, abs_filename)

    return GherkinDocument.from_dict(gherkin_data)


def _description_step_keywords(language: str) -> tuple[str, ...]:
    """Return the step keywords for ``language`` as Gherkin itself defines them.

    Reusing the dialect keywords means the check follows the same logic Gherkin
    uses to recognise steps, so it works for every language Gherkin supports
    rather than English alone. The generic ``*`` keyword is omitted: it only
    opens a step inside a scenario, and matching it against a description would
    flag an ordinary bullet list.
    """
    dialect = Dialect.for_name(language)
    if dialect is None:
        return ()
    keywords = (
        dialect.given_keywords
        + dialect.when_keywords
        + dialect.then_keywords
        + dialect.and_keywords
        + dialect.but_keywords
    )
    return tuple(keyword for keyword in keywords if keyword.strip() != "*")


def _raise_if_step_in_feature_description(
    gherkin_data: Mapping[str, Any], feature_file_text: str, abs_filename: str
) -> None:
    """Raise a FeatureError if a step keyword sits before the first scenario or background.

    Older gherkin-official versions raised a parse error in this case; newer ones
    (>= 31) fold the offending line into the feature description instead. We detect
    it here so the behaviour stays consistent across gherkin-official versions (#779).
    """
    feature = gherkin_data.get("feature")
    if not feature:
        return
    description = feature.get("description") or ""
    non_empty_lines = [line for line in description.splitlines() if line.strip()]
    if not non_empty_lines:
        return
    # A step keyword is only misplaced when it opens the description. A keyword that
    # appears later is legitimate free-text inside a multi-line description.
    first_line = non_empty_lines[0].strip()
    step_keywords = _description_step_keywords(feature.get("language", "en"))
    if not any(first_line.startswith(keyword) for keyword in step_keywords):
        return
    for lineno, file_line in enumerate(feature_file_text.splitlines(), start=1):
        if file_line.strip() == first_line:
            raise exceptions.FeatureError(
                "Step definition outside of a Scenario or a Background.",
                lineno,
                file_line,
                abs_filename,
            )
    raise exceptions.FeatureError(
        "Step definition outside of a Scenario or a Background.",
        feature["location"]["line"],
        first_line,
        abs_filename,
    )


def handle_gherkin_parser_error(
    raw_error: str, line: int, line_content: str, filename: str, original_exception: Exception | None = None
) -> None:
    """Map the error message to a specific exception type and raise it."""
    # Split the raw_error into individual lines
    error_lines = raw_error.splitlines()

    # Check each line against all error patterns
    for error_line in error_lines:
        for pattern, exception_class, message in ERROR_PATTERNS:
            if pattern.search(error_line):
                # If a match is found, raise the corresponding exception with the formatted message
                if original_exception:
                    raise exception_class(message, line, line_content, filename) from original_exception
                else:
                    raise exception_class(message, line, line_content, filename)
