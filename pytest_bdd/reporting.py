"""Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any, Callable

    from _pytest.fixtures import FixtureRequest
    from _pytest.nodes import Item
    from _pytest.reports import TestReport
    from _pytest.runner import CallInfo

    from .parser import Feature, Scenario, Step


class StepReport:
    """Step execution report."""

    failed = False
    stopped = None

    def __init__(self, step: Step) -> None:
        """Step report constructor.

        :param pytest_bdd.parser.Step step: Step.
        """
        self.step = step
        self.started = time.perf_counter()

    def serialize(self) -> dict[str, Any]:
        """Serialize the step execution report.

        :return: Serialized step execution report.
        :rtype: dict
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
        :param node: pytest test node object
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

    def serialize(self) -> dict[str, Any]:
        """Serialize scenario execution report in order to transfer reporting from nodes in the distributed mode.

        :return: Serialized report.
        :rtype: dict
        """
        scenario = self.scenario
        feature = scenario.feature

        return {
            "steps": [step_report.serialize() for step_report in self.step_reports],
            "name": scenario.name,
            "line_number": scenario.line_number,
            "tags": sorted(scenario.tags),
            "feature": {
                "name": feature.name,
                "filename": feature.filename,
                "rel_filename": feature.rel_filename,
                "line_number": feature.line_number,
                "description": feature.description,
                "tags": sorted(feature.tags),
            },
        }

    def fail(self) -> None:
        """Stop collecting information and finalize the report as failed."""
        self.current_step_report.finalize(failed=True)
        remaining_steps = self.scenario.steps[len(self.step_reports) :]

        # Fail the rest of the steps and make reports.
        for step in remaining_steps:
            report = StepReport(step=step)
            report.finalize(failed=True)
            self.add_step_report(report)


def runtest_makereport(item: Item, call: CallInfo, rep: TestReport) -> None:
    """Store item in the report object."""
    try:
        scenario_report: ScenarioReport = item.__scenario_report__
    except AttributeError:
        pass
    else:
        rep.scenario = scenario_report.serialize()
        rep.item = {"name": item.name}


def before_scenario(request: FixtureRequest, feature: Feature, scenario: Scenario) -> None:
    """Create scenario report for the item."""
    request.node.__scenario_report__ = ScenarioReport(scenario=scenario)


def step_error(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable,
    step_func_args: dict,
    exception: Exception,
) -> None:
    """Finalize the step report as failed."""
    request.node.__scenario_report__.fail()


def before_step(request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, step_func: Callable) -> None:
    """Store step start time."""
    request.node.__scenario_report__.add_step_report(StepReport(step=step))


def after_step(
    request: FixtureRequest,
    feature: Feature,
    scenario: Scenario,
    step: Step,
    step_func: Callable,
    step_func_args: dict,
) -> None:
    """Finalize the step report as successful."""
    request.node.__scenario_report__.current_step_report.finalize(failed=False)
