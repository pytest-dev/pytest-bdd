# Refactor to Enums
import re
from collections import defaultdict

TAG = "tag"
FEATURE = "feature"
SCENARIO_OUTLINE = "scenario outline"
EXAMPLES = "examples"
EXAMPLES_VERTICAL = "examples vertical"
SCENARIO = "scenario"
BACKGROUND = "background"
EXAMPLES_HEADERS = "example headers"
EXAMPLE_LINE = "example line"
EXAMPLE_LINE_VERTICAL = "example line vertical"
GIVEN = "given"
WHEN = "when"
THEN = "then"


class StepType:
    CONTEXT = "Context"
    ACTION = "Action"
    OUTCOME = "Outcome"
    CONJUNCTION = "Conjunction"
    UNSPECIFIED = "Unspecified"
    UNKNOWN = "Unknown"


STEP_PREFIXES = {
    FEATURE: "Feature: ",
    SCENARIO_OUTLINE: "Scenario Outline: ",
    EXAMPLES_VERTICAL: "Examples: Vertical",
    EXAMPLES: "Examples:",
    SCENARIO: "Scenario: ",
    BACKGROUND: "Background:",
    GIVEN: "Given ",
    WHEN: "When ",
    THEN: "Then ",
    TAG: "@",
}
STEP_TYPE_BY_NORMALIZED_PREFIX = defaultdict(
    lambda: StepType.UNKNOWN,
    {
        "given": StepType.CONTEXT,
        "when": StepType.ACTION,
        "then": StepType.OUTCOME,
        "and": StepType.CONJUNCTION,
        "but": StepType.CONJUNCTION,
        "*": StepType.CONJUNCTION,
    },
)
PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")

TYPE_KEYWORD_TYPE = defaultdict(
    lambda: StepType.UNKNOWN,
    {
        "And": StepType.CONJUNCTION,
        "But": StepType.CONJUNCTION,
        "*": StepType.UNSPECIFIED,
        "Given": StepType.CONTEXT,
        "When": StepType.ACTION,
        "Then": StepType.OUTCOME,
    },
)
