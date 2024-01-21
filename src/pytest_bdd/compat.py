from __future__ import annotations

from collections.abc import Sequence
from importlib.metadata import version

from _pytest.fixtures import FixtureDef, FixtureManager
from _pytest.nodes import Node
from packaging.version import Version
from packaging.version import parse as parse_version

pytest_version = parse_version(version("pytest"))


if pytest_version >= Version("8.1"):

    def getfixturedefs(fixturemanager: FixtureManager, fixturename: str, node: Node) -> Sequence[FixtureDef] | None:
        return fixturemanager.getfixturedefs(fixturename, node)

else:

    def getfixturedefs(fixturemanager: FixtureManager, fixturename: str, node: Node) -> Sequence[FixtureDef] | None:
        return fixturemanager.getfixturedefs(fixturename, node.nodeid)
