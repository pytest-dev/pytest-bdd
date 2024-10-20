"""Reporting functionality.

Collection of the scenario execution statuses, timing, and other information
that enriches the pytest test reporting.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.nodes import Item
    from _pytest.reports import TestReport
    from _pytest.runner import CallInfo

    from .parser import Feature, Scenario, Step


class StepReport:
    """Step execution report."""

    def __init__(self, step: Step) -> None:
        """Initialize StepReport.

        :param step: Step object.
        """
        self.step = step
        self.started = time.perf_counter()
        self.failed = False
        self.stopped = None

    def serialize(self) -> dict[str, Any]:
        """Serialize the step report.

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
        """Finalize the step report.

        :param failed: Whether the step failed.
        """
        self.stopped = time.perf_counter()
        self.failed = failed

    @property
    def duration(self) -> float:
        """Return step execution duration.

        :return: Execution duration.
        """
        if self.stopped is None:
            return 0
        return self.stopped - self.started


class ScenarioReport:
    """Scenario execution report."""

    def __init__(self, scenario: Scenario) -> None:
        """Initialize ScenarioReport.

        :param scenario: Scenario object.
        """
        self.scenario = scenario
        self.step_reports: list[StepReport] = []

    @property
    def current_step_report(self) -> StepReport:
        """Return the current step report.

        :return: The current step report.
        """
        return self.step_reports[-1]

    def add_step_report(self, step_report: StepReport) -> None:
        """Add a new step report.

        :param step_report: StepReport object.
        """
        self.step_reports.append(step_report)

    def serialize(self) -> dict[str, Any]:
        """Serialize the scenario report.

        :return: Serialized scenario report.
        """
        scenario = self.scenario
        feature = scenario.feature

        serialized = {
            "steps": [step_report.serialize() for step_report in self.step_reports],
            "keyword": scenario.keyword,
            "name": scenario.name,
            "line_number": scenario.line_number,
            "tags": sorted(scenario.tags),
            "feature": {
                "keyword": feature.keyword,
                "name": feature.name,
                "filename": feature.filename,
                "rel_filename": feature.rel_filename,
                "line_number": feature.line_number,
                "description": feature.description,
                "tags": sorted(feature.tags),
            },
        }

        # Include rule information if present
        if scenario.rule:
            serialized["rule"] = {
                "keyword": scenario.rule.keyword,
                "name": scenario.rule.name,
                "description": scenario.rule.description,
                "tags": sorted(scenario.rule.tags),
            }

        return serialized

    def fail(self) -> None:
        """Mark the scenario as failed and finalize remaining steps."""
        self.current_step_report.finalize(failed=True)
        remaining_steps = self.scenario.steps[len(self.step_reports) :]

        # Fail the rest of the steps and create reports
        for step in remaining_steps:
            report = StepReport(step=step)
            report.finalize(failed=True)
            self.add_step_report(report)


# Reporting Hooks


def runtest_makereport(item: Item, call: CallInfo, rep: TestReport) -> None:
    """Store scenario report in the test report."""
    scenario_report = getattr(item, "__scenario_report__", None)
    if scenario_report:
        rep.scenario = scenario_report.serialize()  # type: ignore
        rep.item = {"name": item.name}  # type: ignore


def before_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario) -> None:
    """Create a new scenario report before running the scenario."""
    request.node.__scenario_report__ = ScenarioReport(scenario=scenario)


def step_error(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., Any],
    step_func_args: dict,
    exception: Exception,
) -> None:
    """Finalize the step report as failed in case of an error."""
    request.node.__scenario_report__.fail()


def before_step(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable[..., Any],
) -> None:
    """Start a new step report before running the step."""
    request.node.__scenario_report__.add_step_report(StepReport(step=step))


def after_step(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable,
    step_func_args: dict,
) -> None:
    """Finalize the step report as successful after the step is executed."""
    request.node.__scenario_report__.current_step_report.finalize(failed=False)
