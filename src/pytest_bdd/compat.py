from __future__ import annotations

from collections.abc import Sequence
from importlib.metadata import version

from _pytest.fixtures import FixtureDef as _FixtureDef
from _pytest.fixtures import FixtureManager
from _pytest.nodes import Node
from packaging.version import parse as parse_version

pytest_version = parse_version(version("pytest"))

__all__ = ["getfixturedefs", "FixtureDef"]

if pytest_version.release >= (8, 1):

    def getfixturedefs(fixturemanager: FixtureManager, fixturename: str, node: Node) -> Sequence[_FixtureDef] | None:
        return fixturemanager.getfixturedefs(fixturename, node)

    def FixtureDef(fixturemanager, **kwargs):
        kwargs.setdefault("config", fixturemanager.config)
        return _FixtureDef(**kwargs)

else:

    def getfixturedefs(fixturemanager: FixtureManager, fixturename: str, node: Node) -> Sequence[FixtureDef] | None:
        return fixturemanager.getfixturedefs(fixturename, node.nodeid)

    FixtureDef = _FixtureDef
