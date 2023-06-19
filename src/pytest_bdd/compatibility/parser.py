from pathlib import Path
from typing import TYPE_CHECKING, Callable, Sequence, Union

from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.compatibility.typing import Protocol, runtime_checkable
from pytest_bdd.utils import PytestBDDIdGeneratorHandler

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.model import Feature


@runtime_checkable
class ParserProtocol(Protocol):
    # Defines which files would be parsed
    glob: Callable[[Path], Sequence[Union[str, Path]]]

    def __init__(self, *args, id_generator=None, **kwargs):  # pragma: no cover
        ...

    def parse(
        self, config: Union[Config, PytestBDDIdGeneratorHandler], path: Path, uri: str, *args, **kwargs
    ) -> "Feature":  # pragma: no cover
        ...
