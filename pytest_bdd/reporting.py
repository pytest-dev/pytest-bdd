"""Reporting functionality.

Collection of the scenario excecution statuses, timing and other information
that enriches the pytest test reporting.
"""

import time
from itertools import chain

from _pytest.mark import ParameterSet

from .utils import get_parametrize_markers


class StepReport:
    """Step excecution report."""

    failed = False
    stopped = None

    def __init__(self, step):
        """Step report constructor.

        :param pytest_bdd.parser.Step step: Step.
        """
        self.step = step
        self.started = time.time()

    def serialize(self):
        """Serialize the step excecution report.

        :return: Serialized step excecution report.
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

    def finalize(self, failed):
        """Stop collecting information and finalize the report.

        :param bool failed: Wheither the step excecution is failed.
        """
        self.stopped = time.time()
        self.failed = failed

    @property
    def duration(self):
        """Step excecution duration.

        :return: Step excecution duration.
        :rtype: float
        """
        if self.stopped is None:
            return 0

        return self.stopped - self.started


class ScenarioReport:
    """Scenario execution report."""

    def __init__(self, scenario, node):
        """Scenario report constructor.

        :param pytest_bdd.parser.Scenario scenario: Scenario.
        :param node: pytest test node object
        """
        self.scenario = scenario
        self.step_reports = []
        self.node = node

    @property
    def current_step_report(self):
        """Get current step report.

        :return: Last or current step report.
        :rtype: pytest_bdd.reporting.StepReport
        """
        return self.step_reports[-1]

    def add_step_report(self, step_report):
        """Add new step report.

        :param step_report: New current step report.
        :type step_report: pytest_bdd.reporting.StepReport
        """
        self.step_reports.append(step_report)

    def serialize(self):
        """Serialize scenario excecution report in order to transfer reportin from nodes in the distributed mode.

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
            **self.serialize_examples(),
        }

    def get_param_index(self, param_names):
        parametrize_args = get_parametrize_markers(self.node)

        for parametrize_arg in parametrize_args:
            arg_param_names = (
                parametrize_arg.names if isinstance(parametrize_arg[0], (tuple, list)) else [parametrize_arg.names]
            )
            param_values = [list(v.values) if isinstance(v, ParameterSet) else v for v in parametrize_arg.values]
            if param_names == arg_param_names:
                node_param_values = [self.node.funcargs[param_name] for param_name in param_names]
                if node_param_values in param_values:
                    return param_values.index(node_param_values)
                elif tuple(node_param_values) in param_values:
                    return param_values.index(tuple(node_param_values))

    def serialize_examples(self):
        return {
            "examples": [
                {
                    "name": example_table.name,
                    "line_number": example_table.line_number,
                    "rows": list(example_table.get_params(self.scenario.example_converters, builtin=True)),
                    "row_index": self.get_param_index(example_table.example_params),
                    "tags": list(example_table.tags),
                }
                for example_table in chain(
                    self.scenario.examples.example_tables, self.scenario.feature.examples.example_tables
                )
            ],
            "example_kwargs": {
                example_param: str(self.node.funcargs[example_param])
                for example_param in self.scenario.get_example_params()
            },
        }

    def fail(self):
        """Stop collecting information and finalize the report as failed."""
        self.current_step_report.finalize(failed=True)
        remaining_steps = self.scenario.steps[len(self.step_reports) :]

        # Fail the rest of the steps and make reports.
        for step in remaining_steps:
            report = StepReport(step=step)
            report.finalize(failed=True)
            self.add_step_report(report)


def runtest_makereport(item, call, rep):
    """Store item in the report object."""
    try:
        scenario_report = item.__scenario_report__
    except AttributeError:
        pass
    else:
        rep.scenario = scenario_report.serialize()
        rep.item = {"name": item.name}


def before_scenario(request, feature, scenario):
    """Create scenario report for the item."""
    request.node.__scenario_report__ = ScenarioReport(scenario=scenario, node=request.node)


def step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Finalize the step report as failed."""
    request.node.__scenario_report__.fail()


def before_step(request, feature, scenario, step, step_func):
    """Store step start time."""
    request.node.__scenario_report__.add_step_report(StepReport(step=step))


def after_step(request, feature, scenario, step, step_func, step_func_args):
    """Finalize the step report as successful."""
    request.node.__scenario_report__.current_step_report.finalize(failed=False)
