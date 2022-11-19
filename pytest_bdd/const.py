import re
from collections import defaultdict

from pytest_bdd.model.messages import Type as StepType

TAG_PREFIX = "@"


STEP_TYPE_TO_STEP_PREFIX = {
    StepType.unknown: "*",
    StepType.outcome: "Then",
    StepType.context: "Given",
    StepType.action: "When",
}

STEP_TYPE_TO_STEP_METHOD_NAME = {
    StepType.unknown: "step",
    StepType.outcome: "then",
    StepType.context: "given",
    StepType.action: "when",
}

PYTHON_REPLACE_REGEX = re.compile(r"\W")
ALPHA_REGEX = re.compile(r"^\d+_*")

TYPE_KEYWORD_TYPE = defaultdict(
    lambda: StepType.unknown,
    {
        "And": StepType.unknown,
        "But": StepType.unknown,
        "*": StepType.unknown,
        "Given": StepType.context,
        "When": StepType.action,
        "Then": StepType.outcome,
    },
)
