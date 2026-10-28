from __future__ import annotations

import contextlib
from collections.abc import Generator, Sequence
from importlib.metadata import version

from _pytest.fixtures import FixtureDef, FixtureManager, FixtureRequest
from _pytest.nodes import Node
from packaging.version import parse as parse_version

pytest_version = parse_version(version("pytest"))

__all__ = ["get_fixture_names", "getfixturedefs", "inject_fixture", "inject_temporary_fixturedefs"]

if pytest_version.release >= (9, 2):

    def get_fixture_names(fixturemanager: FixtureManager) -> list[str]:
        """Return the names of all the fixtures registered in the fixture manager, regardless of their visibility.

        The result is a copy, so it is safe to iterate over it while fixtures get registered or removed.
        Use `getfixturedefs` to find out which definitions of a name are visible to a given node.
        """
        # pytest>=9.2 keeps the registry as `name -> {node -> [fixturedefs]}`.
        # Plugins still using the deprecated nodeid-based registration API end up in a separate registry
        # (`name -> {nodeid -> [fixturedefs]}`), which pytest's own `getfixturedefs` also consults,
        # so we need to include its names too. A name can be in both, hence the de-duplication.
        return list(
            dict.fromkeys(
                [
                    *fixturemanager._arg2node2fixturedefs,  # type: ignore
                    *fixturemanager._arg2nodeid2fixturedefs,  # type: ignore
                ]
            )
        )

    @contextlib.contextmanager
    def inject_temporary_fixturedefs(
        fixturemanager: FixtureManager, name: str, fixturedefs: list[FixtureDef[object]], node: Node
    ) -> Generator[None]:
        """Temporarily register the fixturedefs under the given name, visible to the given node.

        This is a context manager: the registration only lasts for the duration of the `with` block.
        `fixturedefs` must be ordered like pytest orders the result of `getfixturedefs`:
        the closest definition (highest priority) last.
        """
        # We register under `node`, so that the fixture is only visible to that node and its children.
        node2fixturedefs = fixturemanager._arg2node2fixturedefs.setdefault(name, {})  # type: ignore
        # `FixtureManager.getfixturedefs` reverses the stored list when `bdd_name` is resolved.
        # `fixturedefs` is ordered with the highest priority last, so we store it reversed to get that order back.
        node2fixturedefs[node] = list(reversed(fixturedefs))
        try:
            yield
        finally:
            # Clean up after ourselves, like `mock.patch` does. The fixture manager lives for the whole session
            # (not just the current test item), so without this every item that uses a step would leave an
            # entry behind (keeping the node alive) until the end of the run.
            # It's not needed for correctness on pytest>=9.2: the entry is keyed by `node`, and pytest only
            # looks at the requesting node and its parents, so other nodes can't see it anyway.
            del fixturemanager._arg2node2fixturedefs[name]  # type: ignore

else:

    def get_fixture_names(fixturemanager: FixtureManager) -> list[str]:
        """Return the names of all the fixtures registered in the fixture manager, regardless of their visibility.

        The result is a copy, so it is safe to iterate over it while fixtures get registered or removed.
        Use `getfixturedefs` to find out which definitions of a name are visible to a given node.
        """
        # pytest<9.2 keeps the registry as `name -> [fixturedefs]`.
        return list(fixturemanager._arg2fixturedefs)  # type: ignore

    @contextlib.contextmanager
    def inject_temporary_fixturedefs(
        fixturemanager: FixtureManager, name: str, fixturedefs: list[FixtureDef[object]], node: Node
    ) -> Generator[None]:
        """Temporarily register the fixturedefs under the given name.

        This is a context manager: the registration only lasts for the duration of the `with` block.
        `node` is unused here, since the registry of these pytest versions isn't keyed by node:
        visibility is decided by each fixturedef's `baseid`.
        """
        fixturemanager._arg2fixturedefs[name] = fixturedefs  # type: ignore
        try:
            yield
        finally:
            # Clean up after ourselves, like `mock.patch` does. The registry is keyed by name only (and lives for
            # the whole session), so without this a stale entry would stay registered under this name.
            del fixturemanager._arg2fixturedefs[name]  # type: ignore


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
        if pytest_version.release >= (9, 1):
            request._fixturemanager._register_fixture(
                name=arg,
                func=lambda: value,
                node=request.node,
            )
        else:
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
