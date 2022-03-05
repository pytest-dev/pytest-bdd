"""Cucumber json output formatter."""
from __future__ import annotations

import json
import math
import os
import time
import typing

if typing.TYPE_CHECKING:
    from typing import Any

    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.reports import TestReport
    from _pytest.terminal import TerminalReporter


def add_options(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Cucumber JSON")
    group.addoption(
        "--cucumberjson",
        "--cucumber-json",
        action="store",
        dest="cucumber_json_path",
        metavar="path",
        default=None,
        help="create cucumber json style report file at given path.",
    )


def configure(config: Config) -> None:
    cucumber_json_path = config.option.cucumber_json_path
    # prevent opening json log on worker nodes (xdist)
    if cucumber_json_path and not hasattr(config, "workerinput"):
        config._bddcucumberjson = LogBDDCucumberJSON(cucumber_json_path)
        config.pluginmanager.register(config._bddcucumberjson)


def unconfigure(config: Config) -> None:
    xml = getattr(config, "_bddcucumberjson", None)
    if xml is not None:
        del config._bddcucumberjson
        config.pluginmanager.unregister(xml)


class LogBDDCucumberJSON:

    """Logging plugin for cucumber like json output."""

    def __init__(self, logfile: str) -> None:
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.features: dict[str, dict] = {}

    def _get_result(self, step: dict[str, Any], report: TestReport, error_message: bool = False) -> dict[str, Any]:
        """Get scenario test run result.

        :param step: `Step` step we get result for
        :param report: pytest `Report` object
        :return: `dict` in form {"status": "<passed|failed|skipped>", ["error_message": "<error_message>"]}
        """
        result: dict[str, Any] = {}
        if report.passed or not step["failed"]:  # ignore setup/teardown
            result = {"status": "passed"}
        elif report.failed and step["failed"]:
            result = {"status": "failed", "error_message": str(report.longrepr) if error_message else ""}
        elif report.skipped:
            result = {"status": "skipped"}
        result["duration"] = int(math.floor((10**9) * step["duration"]))  # nanosec
        return result

    def _serialize_tags(self, item: dict[str, Any]) -> list[dict[str, Any]]:
        """Serialize item's tags.

        :param item: json-serialized `Scenario` or `Feature`.
        :return: `list` of `dict` in the form of:
            [
                {
                    "name": "<tag>",
                    "line": 2,
                }
            ]
        """
        return [{"name": tag, "line": item["line_number"] - 1} for tag in item["tags"]]

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        try:
            scenario = report.scenario
        except AttributeError:
            # skip reporting for non-bdd tests
            return

        if not scenario["steps"] or report.when != "call":
            # skip if there isn't a result or scenario has no steps
            return

        def stepmap(step: dict[str, Any]) -> dict[str, Any]:
            error_message = False
            if step["failed"] and not scenario.setdefault("failed", False):
                scenario["failed"] = True
                error_message = True

            step_name = step["name"]

            return {
                "keyword": step["keyword"],
                "name": step_name,
                "line": step["line_number"],
                "match": {"location": ""},
                "result": self._get_result(step, report, error_message),
            }

        if scenario["feature"]["filename"] not in self.features:
            self.features[scenario["feature"]["filename"]] = {
                "keyword": "Feature",
                "uri": scenario["feature"]["rel_filename"],
                "name": scenario["feature"]["name"] or scenario["feature"]["rel_filename"],
                "id": scenario["feature"]["rel_filename"].lower().replace(" ", "-"),
                "line": scenario["feature"]["line_number"],
                "description": scenario["feature"]["description"],
                "tags": self._serialize_tags(scenario["feature"]),
                "elements": [],
            }

        self.features[scenario["feature"]["filename"]]["elements"].append(
            {
                "keyword": "Scenario",
                "id": report.item["name"],
                "name": scenario["name"],
                "line": scenario["line_number"],
                "description": "",
                "tags": self._serialize_tags(scenario),
                "type": "scenario",
                "steps": [stepmap(step) for step in scenario["steps"]],
            }
        )

    def pytest_sessionstart(self) -> None:
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self) -> None:
        with open(self.logfile, "w", encoding="utf-8") as logfile:
            logfile.write(json.dumps(list(self.features.values())))

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        terminalreporter.write_sep("-", f"generated json file: {self.logfile}")
