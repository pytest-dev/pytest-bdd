"""Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, TypedDict
from weakref import WeakKeyDictionary

from typing_extensions import NotRequired

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.nodes import Item
    from _pytest.reports import TestReport
    from _pytest.runner import CallInfo

    from .parser import Feature, Scenario, Step

scenario_reports_registry: WeakKeyDictionary[Item, ScenarioReport] = WeakKeyDictionary()
test_report_context_registry: WeakKeyDictionary[TestReport, ReportContext] = WeakKeyDictionary()


class FeatureDict(TypedDict):
    keyword: str
    name: str
    filename: str
    rel_filename: str
    language: str
    line_number: int
    description: str
    tags: list[str]


class RuleDict(TypedDict):
    keyword: str
    name: str
    description: str
    tags: list[str]


class StepReportDict(TypedDict):
    name: str
    type: str
    keyword: str
    line_number: int
    failed: bool
    duration: float


class ScenarioReportDict(TypedDict):
    steps: list[StepReportDict]
    keyword: str
    name: str
    line_number: int
    tags: list[str]
    feature: FeatureDict
    description: str
    rule: NotRequired[RuleDict]
    failed: NotRequired[bool]


class StepReport:
    """Step execution report."""

    failed: bool = False
    stopped: float | None = None

    def __init__(self, step: Step) -> None:
        """Step report constructor.

        :param pytest_bdd.parser.Step step: Step.
        """
        self.step = step
        self.started = time.perf_counter()

    def serialize(self) -> StepReportDict:
        """Serialize the step execution report.

        :return: Serialized step execution report.
        """
        return {
            "name": self.step.name,
            "type": self.step.type,
            "keyword": self.step.keyword,
            "line_number": self.step.line_number,
            "failed": self.failed,
            "duration": self.duration,
        }

    def finalize(self, failed: bool) -> None:
        """Stop collecting information and finalize the report.

        :param bool failed: Whether the step execution is failed.
        """
        self.stopped = time.perf_counter()
        self.failed = failed

    @property
    def duration(self) -> float:
        """Step execution duration.

        :return: Step execution duration.
        :rtype: float
        """
        if self.stopped is None:
            return 0

        return self.stopped - self.started


class ScenarioReport:
    """Scenario execution report."""

    def __init__(self, scenario: Scenario) -> None:
        """Scenario report constructor.

        :param pytest_bdd.parser.Scenario scenario: Scenario.
        """
        self.scenario: Scenario = scenario
        self.step_reports: list[StepReport] = []

    @property
    def current_step_report(self) -> StepReport:
        """Get current step report.

        :return: Last or current step report.
        :rtype: pytest_bdd.reporting.StepReport
        """
        return self.step_reports[-1]

    def add_step_report(self, step_report: StepReport) -> None:
        """Add new step report.

        :param step_report: New current step report.
        :type step_report: pytest_bdd.reporting.StepReport
        """
        self.step_reports.append(step_report)

    def serialize(self) -> ScenarioReportDict:
        """Serialize scenario execution report in order to transfer reporting from nodes in the distributed mode.

        :return: Serialized report.
        """
        scenario = self.scenario
        feature = scenario.feature

        serialized: ScenarioReportDict = {
            "steps": [step_report.serialize() for step_report in self.step_reports],
            "keyword": scenario.keyword,
            "name": scenario.name,
            "line_number": scenario.line_number,
            "tags": sorted(scenario.tags),
            "description": scenario.description,
            "feature": {
                "keyword": feature.keyword,
                "name": feature.name,
                "filename": feature.filename,
                "rel_filename": feature.rel_filename,
                "language": feature.language,
                "line_number": feature.line_number,
                "description": feature.description,
                "tags": sorted(feature.tags),
            },
        }

        if scenario.rule:
            rule_dict: RuleDict = {
                "keyword": scenario.rule.keyword,
                "name": scenario.rule.name,
                "description": scenario.rule.description,
                "tags": sorted(scenario.rule.tags),
            }
            serialized["rule"] = rule_dict

        return serialized

    def fail(self) -> None:
        """Stop collecting information and finalize the report as failed."""
        self.current_step_report.finalize(failed=True)
        remaining_steps = self.scenario.steps[len(self.step_reports) :]

        # Fail the rest of the steps and make reports.
        for step in remaining_steps:
            report = StepReport(step=step)
            report.finalize(failed=True)
            self.add_step_report(report)


@dataclass
class ReportContext:
    scenario: ScenarioReportDict
    name: str


def runtest_makereport(item: Item, call: CallInfo, rep: TestReport) -> None:
    """Store item in the report object."""
    try:
        scenario_report: ScenarioReport = scenario_reports_registry[item]
    except KeyError:
        return

    test_report_context_registry[rep] = ReportContext(scenario=scenario_report.serialize(), name=item.name)


def before_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario) -> None:
    """Create scenario report for the item."""
    scenario_reports_registry[request.node] = ScenarioReport(scenario=scenario)


def step_error(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., object],
    step_func_args: dict[str, object],
    exception: Exception,
) -> None:
    """Finalize the step report as failed."""
    scenario_reports_registry[request.node].fail()


def before_step(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., object],
) -> None:
    """Store step start time."""
    scenario_reports_registry[request.node].add_step_report(StepReport(step=step))


def after_step(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable,
    step_func_args: dict,
) -> None:
    """Finalize the step report as successful."""
    scenario_reports_registry[request.node].current_step_report.finalize(failed=False)
