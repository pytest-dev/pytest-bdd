from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from pytest_bdd.typing import Protocol, runtime_checkable

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.model.feature import Feature


@runtime_checkable
class ParserProtocol(Protocol):
    glob: Callable[[Path], list[str | Path]]

    def parse(self, path: Path, uri: str, *args, **kwargs) -> Feature:  # pragma: no cover
        ...
