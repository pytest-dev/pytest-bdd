from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
from weakref import WeakKeyDictionary

if TYPE_CHECKING:
    from _pytest.reports import TestReport

    from pytest_bdd.reporting import ReportContext

test_report_context: WeakKeyDictionary[TestReport, ReportContext] = WeakKeyDictionary()
