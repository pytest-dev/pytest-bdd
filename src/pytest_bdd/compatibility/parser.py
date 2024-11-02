from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional, Protocol, Tuple, Union, runtime_checkable

from attr import attrib, attrs

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.utils import IdGenerator, PytestBDDIdGeneratorHandler

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.model import Feature


@runtime_checkable
@attrs
class ParserProtocol(Protocol):
    id_generator: Optional[IdGenerator] = attrib(default=None, kw_only=True)
    # Defines which files would be parsed
    glob: Callable[[Path], Sequence[Union[str, Path]]]

    def parse(
        self, config: Union[Config, PytestBDDIdGeneratorHandler], path: Path, uri: str, *args, **kwargs
    ) -> tuple["Feature", str]:  # pragma: no cover
        ...
