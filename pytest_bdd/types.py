"""Common type definitions."""

FEATURE = "feature"
SCENARIO_OUTLINE = "scenario outline"
EXAMPLES = "examples"
EXAMPLES_VERTICAL = "examples vertical"
EXAMPLES_HEADERS = "example headers"
EXAMPLE_LINE = "example line"
EXAMPLE_LINE_VERTICAL = "example line vertical"
SCENARIO = "scenario"
BACKGROUND = "background"
GIVEN = "given"
WHEN = "when"
THEN = "then"
AND_AND = "and_and"
AND_BUT = "and_but"
AND_STAR = "and_star"
TAG = "tag"

CONTINUATION_STEP_TYPES = (AND_AND, AND_BUT, AND_STAR)
STEP_TYPES = (GIVEN, WHEN, THEN, *CONTINUATION_STEP_TYPES)
