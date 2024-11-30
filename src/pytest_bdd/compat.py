from __future__ import annotations

from collections.abc import Sequence
from importlib.metadata import version

from _pytest.fixtures import FixtureDef, FixtureManager, FixtureRequest
from _pytest.nodes import Node
from packaging.version import parse as parse_version

pytest_version = parse_version(version("pytest"))

__all__ = ["getfixturedefs", "inject_fixture"]

if pytest_version.release >= (8, 1):

    def getfixturedefs(
        fixturemanager: FixtureManager, fixturename: str, node: Node
    ) -> Sequence[FixtureDef[object]] | None:
        return fixturemanager.getfixturedefs(fixturename, node)

    def inject_fixture(request: FixtureRequest, arg: str, value: object) -> None:
        """Inject fixture into pytest fixture request.

        :param request: pytest fixture request
        :param arg: argument name
        :param value: argument value
        """
        # Ensure there's a fixture definition for the argument
        request._fixturemanager._register_fixture(
            name=arg,
            func=lambda: value,
            nodeid=request.node.nodeid,
        )
        # Note the fixture we just registered will have a lower priority
        # if there was already one registered, so we need to force its value
        # to the one we want to inject.
        fixture_def = request._get_active_fixturedef(arg)
        fixture_def.cached_result = (value, None, None)  # type: ignore

else:

    def getfixturedefs(
        fixturemanager: FixtureManager, fixturename: str, node: Node
    ) -> Sequence[FixtureDef[object]] | None:
        return fixturemanager.getfixturedefs(fixturename, node.nodeid)  # type: ignore

    def inject_fixture(request: FixtureRequest, arg: str, value: object) -> None:
        """Inject fixture into pytest fixture request.

        :param request: pytest fixture request
        :param arg: argument name
        :param value: argument value
        """
        fd = FixtureDef(
            fixturemanager=request._fixturemanager,  # type: ignore
            baseid=None,
            argname=arg,
            func=lambda: value,
            scope="function",
            params=None,
        )
        fd.cached_result = (value, 0, None)

        old_fd = request._fixture_defs.get(arg)
        add_fixturename = arg not in request.fixturenames

        def fin() -> None:
            request._fixturemanager._arg2fixturedefs[arg].remove(fd)

            if old_fd is not None:
                request._fixture_defs[arg] = old_fd

            if add_fixturename:
                request._pyfuncitem._fixtureinfo.names_closure.remove(arg)

        request.addfinalizer(fin)

        # inject fixture definition
        request._fixturemanager._arg2fixturedefs.setdefault(arg, []).append(fd)

        # inject fixture value in request cache
        request._fixture_defs[arg] = fd
        if add_fixturename:
            request._pyfuncitem._fixtureinfo.names_closure.append(arg)
