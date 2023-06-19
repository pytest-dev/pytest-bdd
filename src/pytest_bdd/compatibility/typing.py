import sys

if sys.version_info >= (3, 10):
    from typing import Literal, Protocol, TypeAlias, runtime_checkable
else:
    from typing import runtime_checkable

    from typing_extensions import Literal, Protocol, TypeAlias

__all__ = [
    "Literal",
    "Protocol",
    "runtime_checkable",
    "TypeAlias",
]
