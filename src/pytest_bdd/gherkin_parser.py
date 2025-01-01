from __future__ import annotations

import copy
import linecache
import re

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.parser_types import Feature, GherkinDocument, Step

from . import exceptions

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


def replace_datatable_values(document: GherkinDocument) -> None:
    """Replace all cell values in DataTables within a GherkinDocument using _to_raw_string."""

    def _to_raw_string(normal_string: str) -> str:
        return normal_string.replace("\\", "\\\\")

    def process_step(step: Step) -> None:
        if "dataTable" in step:
            for row in step["dataTable"]["rows"]:
                for cell in row["cells"]:
                    cell["value"] = _to_raw_string(cell["value"])

    def process_feature(feature: Feature) -> None:
        for child in feature["children"]:
            if "background" in child:
                for step in child["background"]["steps"]:  # type: ignore[typeddict-item]
                    process_step(step)
            elif "scenario" in child:
                scenario = child["scenario"]  # type: ignore[typeddict-item]
                for step in scenario["steps"]:
                    process_step(step)
                for example in scenario["examples"]:
                    for row in example["tableBody"]:
                        for cell in row["cells"]:
                            cell["value"] = _to_raw_string(cell["value"])
            elif "rule" in child:
                rule = child["rule"]  # type: ignore[typeddict-item]
                for rule_child in rule["children"]:
                    if "background" in rule_child:
                        for step in rule_child["background"]["steps"]:
                            process_step(step)
                    elif "scenario" in rule_child:
                        scenario = rule_child["scenario"]
                        for step in scenario["steps"]:
                            process_step(step)
                        for example in scenario["examples"]:
                            for row in example["tableBody"]:
                                for cell in row["cells"]:
                                    cell["value"] = _to_raw_string(cell["value"])

    if "feature" in document:
        process_feature(document["feature"])


def get_gherkin_document(abs_filename: str, encoding: str = "utf-8") -> GherkinDocument:
    with open(abs_filename, encoding=encoding) as f:
        feature_file_text = f.read()

    try:
        raw_gherkin_data = Parser().parse(feature_file_text)
    except CompositeParserException as e:
        message = e.args[0]
        line = e.errors[0].location["line"]
        line_content = linecache.getline(abs_filename, e.errors[0].location["line"]).rstrip("\n")
        filename = abs_filename
        handle_gherkin_parser_error(message, line, line_content, filename, e)
        # If no patterns matched, raise a generic GherkinParserError
        raise exceptions.GherkinParseError(f"Unknown parsing error: {message}", line, line_content, filename) from e

    gherkin_data = copy.deepcopy(raw_gherkin_data)
    # Apply pytest-bdd formatting rules to the document
    replace_datatable_values(gherkin_data)

    return gherkin_data


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
