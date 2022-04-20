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


class STEP_TYPE:
    GIVEN = "given"
    WHEN = "when"
    THEN = "then"
    AND = "and"
    OTHER = "other"


STEP_PREFIXES = {
    FEATURE: "Feature: ",
    SCENARIO_OUTLINE: "Scenario Outline: ",
    EXAMPLES_VERTICAL: "Examples: Vertical",
    EXAMPLES: "Examples:",
    SCENARIO: "Scenario: ",
    BACKGROUND: "Background:",
    STEP_TYPE.GIVEN: "Given ",
    STEP_TYPE.WHEN: "When ",
    STEP_TYPE.THEN: "Then ",
    TAG: "@",
}
STEP_TYPES_BY_NORMALIZED_PREFIX = defaultdict(
    lambda: STEP_TYPE.OTHER,
    {
        "given": STEP_TYPE.GIVEN,
        "when": STEP_TYPE.WHEN,
        "then": STEP_TYPE.THEN,
        "and": STEP_TYPE.AND,
        "but": STEP_TYPE.AND,
        "*": STEP_TYPE.AND,
    },
)
PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")
