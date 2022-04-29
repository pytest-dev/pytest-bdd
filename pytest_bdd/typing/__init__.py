"""Common type definitions."""
from __future__ import annotations

import sys

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable

assert Protocol
assert runtime_checkable
