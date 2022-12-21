from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Callable

from pytest_bdd.typing import Protocol, runtime_checkable
from pytest_bdd.typing.pytest import Config
from pytest_bdd.utils import PytestBDDIdGeneratorHandler

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.model import Feature


@runtime_checkable
class ParserProtocol(Protocol):
    glob: Callable[[Path], list[str | Path]]

    def parse(
        self, config: Config | PytestBDDIdGeneratorHandler, path: Path, uri: str, *args, **kwargs
    ) -> Feature:  # pragma: no cover
        ...
