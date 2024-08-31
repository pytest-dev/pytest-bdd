"""
Compatibility module for pytest
"""
from __future__ import annotations

import sys
from operator import ge
from pathlib import Path
from typing import TYPE_CHECKING, cast

from _pytest.config import Config, PytestPluginManager
from _pytest.config.argparsing import Parser
from _pytest.fixtures import FixtureDef, FixtureLookupError, call_fixture_func
from _pytest.main import Session, wrap_session
from _pytest.mark import Mark, MarkDecorator
from _pytest.python import Metafunc
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.terminal import TerminalReporter
from pytest import Module as PytestModule
from pytest import fail as _pytest_fail

from pytest_bdd.packaging import compare_distribution_version

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

__all__ = [
    "assert_outcomes",
    "Item",
    "CallInfo",
    "call_fixture_func",
    "Config",
    "ExitCode",
    "FixtureDef",
    "FixtureLookupError",
    "FixtureRequest",
    "get_config_root_path",
    "Mark",
    "MarkDecorator",
    "Metafunc",
    "Module",
    "Parser",
    "PytestPluginManager",
    "PYTEST6",
    "PYTEST7",
    "RunResult",
    "Session",
    "TerminalReporter",
    "Testdir",
    "TestReport",
    "TypeAlias",
    "wrap_session",
]


# region pytest version dependent imports
def is_pytest_version_greater_or_equal(version: str):
    return compare_distribution_version("pytest", version, ge)


PYTEST6, PYTEST61, PYTEST62, PYTEST7, PYTEST8, PYTEST81, PYTEST83 = map(
    is_pytest_version_greater_or_equal,
    [
        "6.0",
        "6.1",
        "6.2",
        "7.0",
        "8.0",
        "8.1",
        "8.3",
    ],
)

if PYTEST6:
    # noinspection PyUnresolvedReferences
    from _pytest.compat import NotSetType
    from _pytest.config import ExitCode

    # noinspection PyUnresolvedReferences
    from _pytest.mark import MarkMatcher

    # noinspection PyUnresolvedReferences
    from _pytest.mark.expression import Expression, ParseError

    __all__ += [
        "MarkMatcher",
        "Expression",
        "ParseError",
    ]
else:
    ExitCode: TypeAlias = int  # type:ignore[no-redef]

if PYTEST7:
    if TYPE_CHECKING:
        from pytest import Testdir
else:
    import py

    if TYPE_CHECKING:
        from _pytest.pytester import Testdir  # type: ignore[no-redef, attr-defined]

if PYTEST62:
    from pytest import FixtureRequest
else:
    from _pytest.fixtures import FixtureRequest
# endregion

if TYPE_CHECKING:  # pragma: no cover
    from _pytest.nodes import Item as BaseItem
    from _pytest.pytester import RunResult

    class Item(BaseItem):
        _request: FixtureRequest

else:
    from _pytest.nodes import Item


class Module(PytestModule):
    @classmethod
    def build(cls, parent, file_path):
        if hasattr(cls, "from_parent"):
            collector = cls.from_parent(
                parent, **(dict(path=Path(file_path)) if PYTEST7 else dict(fspath=py.path.local(file_path)))
            )
        else:
            collector = cls(parent=parent, fspath=py.path.local(file_path))
        return collector

    def get_path(self):
        return getattr(self, "path", Path(self.fspath))


if PYTEST6:

    def assert_outcomes(
        result: RunResult,
        passed: int = 0,
        skipped: int = 0,
        failed: int = 0,
        errors: int = 0,
        xpassed: int = 0,
        xfailed: int = 0,
    ) -> None:
        """Compatibility function for result.assert_outcomes"""
        result.assert_outcomes(
            errors=errors, passed=passed, skipped=skipped, failed=failed, xpassed=xpassed, xfailed=xfailed
        )

else:

    def assert_outcomes(
        result: RunResult,
        passed: int = 0,
        skipped: int = 0,
        failed: int = 0,
        errors: int = 0,
        xpassed: int = 0,
        xfailed: int = 0,
    ) -> None:
        """Compatibility function for result.assert_outcomes"""
        result.assert_outcomes(  # type: ignore[call-arg]
            #  Pytest < 6 uses the singular form
            error=errors,
            passed=passed,
            skipped=skipped,
            failed=failed,
            xpassed=xpassed,
            xfailed=xfailed,
        )


def get_config_root_path(config: Config) -> Path:
    return Path(getattr(cast(Config, config), "rootpath" if PYTEST61 else "rootdir"))


def fail(reason, pytrace=True):
    __tracebackhide__ = True
    if PYTEST7:
        return _pytest_fail(reason, pytrace=pytrace)
    else:
        return _pytest_fail(msg=reason, pytrace=pytrace)


if PYTEST6:

    def is_set(obj):
        return not isinstance(obj, NotSetType)

else:

    def is_set(obj):
        return type(obj) is not object


def get_metafunc_call_arg(call, arg):
    return call.params[arg] if PYTEST8 else call.funcargs[arg]
