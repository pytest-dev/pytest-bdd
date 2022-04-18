"""Reporting functionality.

Collection of the scenario execution statuses, timing and other information
that enriches the pytest test reporting.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from attr import Factory, attrib, attrs

from .feature import Feature
from .pickle import Pickle, Step

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Callable

    from _pytest.fixtures import FixtureRequest
    from _pytest.runner import CallInfo

    from .types import Item, TestReport


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
    pickle: Pickle = attrib()
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
        pickle = self.pickle
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
        remaining_steps = self.pickle.steps[len(self.step_reports) :]

        # Fail the rest of the steps and make reports.
        for step in remaining_steps:
            report = StepReport(step=step)
            report.finalize(failed=True)
            self.add_step_report(report)


def runtest_makereport(item: Item, call: CallInfo, rep: TestReport) -> None:
    """Store item in the report object."""
    try:
        scenario_report: ScenarioReport = item.__pytest_bdd_scenario_report__
    except AttributeError:
        pass
    else:
        rep.scenario = scenario_report.serialize()
        rep.item = {"name": item.name}


def before_scenario(request: FixtureRequest, feature: Feature, scenario: Pickle) -> None:
    """Create scenario report for the item."""
    # TODO chek usages
    request.node.__pytest_bdd_scenario_report__ = ScenarioReport(  # type: ignore[call-arg]
        feature=feature, pickle=scenario
    )


def step_error(
    request: FixtureRequest,
    feature: Feature,
    scenario: Pickle,
    step: Step,
    step_func: Callable,
    step_func_args: dict,
    exception: Exception,
) -> None:
    """Finalize the step report as failed."""
    request.node.__pytest_bdd_scenario_report__.fail()


def before_step(request: FixtureRequest, feature: Feature, scenario: Pickle, step: Step, step_func: Callable) -> None:
    """Store step start time."""
    request.node.__pytest_bdd_scenario_report__.add_step_report(StepReport(step=step))


def after_step(
    request: FixtureRequest,
    feature: Feature,
    scenario: Pickle,
    step: Step,
    step_func: Callable,
    step_func_args: dict,
) -> None:
    """Finalize the step report as successful."""
    request.node.__pytest_bdd_scenario_report__.current_step_report.finalize(failed=False)
