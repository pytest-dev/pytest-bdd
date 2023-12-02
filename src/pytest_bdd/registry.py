from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable
from weakref import WeakKeyDictionary

if TYPE_CHECKING:
    from _pytest.nodes import Item
    from _pytest.reports import TestReport

    from pytest_bdd.reporting import ReportContext, ScenarioReport
    from pytest_bdd.steps import StepFunctionContext

scenario_reports: WeakKeyDictionary[Item, ScenarioReport] = WeakKeyDictionary()
step_function_marker_context: WeakKeyDictionary[Callable[..., Any], StepFunctionContext] = WeakKeyDictionary()
test_report_context: WeakKeyDictionary[TestReport, ReportContext] = WeakKeyDictionary()
