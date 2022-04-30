"""
Compatibility module for pytest
"""
from __future__ import annotations

import sys
from operator import ge
from typing import TYPE_CHECKING

from _pytest.config import Config, PytestPluginManager
from _pytest.config.argparsing import Parser
from _pytest.fixtures import FixtureDef, FixtureLookupError, call_fixture_func
from _pytest.main import Session, wrap_session
from _pytest.mark import Mark, MarkDecorator
from _pytest.python import Metafunc
from _pytest.reports import TestReport
from _pytest.runner import CallInfo
from _pytest.terminal import TerminalReporter

from pytest_bdd.packaging import compare_distribution_version

assert all(
    [
        CallInfo,
        call_fixture_func,
        Config,
        FixtureDef,
        FixtureLookupError,
        Mark,
        MarkDecorator,
        Metafunc,
        Parser,
        PytestPluginManager,
        Session,
        TerminalReporter,
        TestReport,
        wrap_session,
    ]
)

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias
assert TypeAlias

# region pytest version dependent imports
if compare_distribution_version("pytest", "7.0", ge):
    if TYPE_CHECKING:  # pragma: no cover
        from pytest import Testdir
else:
    if TYPE_CHECKING:  # pragma: no cover
        from _pytest.pytester import Testdir  # type: ignore[no-redef, attr-defined]

if compare_distribution_version("pytest", "6.2", ge):
    from pytest import FixtureRequest
else:
    from _pytest.fixtures import FixtureRequest
assert FixtureRequest

# endregion

if TYPE_CHECKING:  # pragma: no cover
    from _pytest.nodes import Item as BaseItem
    from _pytest.pytester import RunResult

    assert RunResult
    assert Testdir

    class Item(BaseItem):
        _request: FixtureRequest

else:
    from _pytest.nodes import Item

    assert Item
assert Item
