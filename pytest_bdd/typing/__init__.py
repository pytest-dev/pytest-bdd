"""Common type definitions."""
from __future__ import annotations

import sys

if sys.version_info >= (3, 8):
    from typing import Literal, Protocol, runtime_checkable
else:
    from typing_extensions import Literal, Protocol, runtime_checkable

__all__ = ["Literal", "Protocol", "runtime_checkable"]
