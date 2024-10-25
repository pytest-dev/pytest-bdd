"""Common type definitions."""

from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from typing_extensions import Literal

GIVEN: Literal["given"] = "given"
WHEN: Literal["when"] = "when"
THEN: Literal["then"] = "then"

STEP_TYPES = (GIVEN, WHEN, THEN)

STEP_TYPE_BY_PARSER_KEYWORD = {
    "Context": GIVEN,
    "Action": WHEN,
    "Outcome": THEN,
}
