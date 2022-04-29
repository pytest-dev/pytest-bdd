"""Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""
from __future__ import annotations

import time
from typing import Any, Callable

import pytest
from attr import Factory, attrib, attrs

from pytest_bdd.model import Feature, Scenario, Step
from pytest_bdd.typing.pytest import CallInfo, FixtureRequest, Item


class StepReport:
    """StepHandler execution report."""

    failed = False
    stopped = None

    def __init__(self, step: Step) -> None:
        """StepHandler report constructor.

        :param StepHandler step: StepHandler.
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
            "type": self.step.prefix,
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
        """StepHandler execution duration.

        :return: StepHandler execution duration.
        :rtype: float
        """
        if self.stopped is None:
            return 0

        return self.stopped - self.started


@attrs
class ScenarioReport:
    """Scenario execution report."""

    feature: Feature = attrib()
    scenario: Scenario = attrib()
    step_reports: list[StepReport] = attrib(default=Factory(list))

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
        pickle = self.scenario
        feature = self.feature

        return {
            "steps": [step_report.serialize() for step_report in self.step_reports],
            "name": pickle.name,
            "line_number": pickle.line_number,
            "tags": sorted(set(pickle.tag_names).difference(feature.tag_names)),
            "feature": {
                "name": feature.name,
                "filename": feature.filename,
                "rel_filename": feature.rel_filename,
                "line_number": feature.line_number,
                "description": feature.description,
                "tags": feature.tag_names,
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


class ScenarioReporterPlugin:
    def __init__(self):
        self.current_report = None

    @pytest.mark.hookwrapper
    def pytest_runtest_makereport(self, item: Item, call: CallInfo):
        outcome = yield
        if call.when != "setup":
            rep = outcome.get_result()
            """Store item in the report object."""
            scenario_report: ScenarioReport = self.current_report

            if scenario_report is not None:
                rep.scenario = scenario_report.serialize()
                rep.item = {"name": item.name}

    @pytest.mark.tryfirst
    def pytest_bdd_before_scenario(self, request: FixtureRequest, feature: Feature, scenario: Scenario) -> None:
        """Create scenario report for the item."""
        self.current_report = ScenarioReport(feature=feature, scenario=scenario)  # type: ignore[call-arg]

    @pytest.mark.tryfirst
    def pytest_bdd_step_error(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        step_func: Callable,
        step_func_args: dict,
        exception: Exception,
    ) -> None:
        """Finalize the step report as failed."""
        self.current_report.fail()

    @pytest.mark.tryfirst
    def pytest_bdd_before_step(
        self, request: FixtureRequest, feature: Feature, scenario: Scenario, step: Step, step_func: Callable
    ) -> None:
        """Store step start time."""
        self.current_report.add_step_report(StepReport(step=step))

    @pytest.mark.tryfirst
    def pytest_bdd_after_step(
        self,
        request: FixtureRequest,
        feature: Feature,
        scenario: Scenario,
        step: Step,
        step_func: Callable,
        step_func_args: dict,
    ) -> None:
        """Finalize the step report as successful."""
        self.current_report.current_step_report.finalize(failed=False)
