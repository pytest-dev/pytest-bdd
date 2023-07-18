"""Cucumber json output formatter."""
import json
import math
import os
import time
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol, Sequence, Union, cast, runtime_checkable

from pydantic import BaseModel, ConfigDict

from pytest_bdd.compatibility.pytest import Parser, TerminalReporter, TestReport

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Config as BaseConfig

    @runtime_checkable
    class LogBDDCucumberJSONProtocol(Protocol):
        _bddcucumberjson: "LogBDDCucumberJSON"

    class Config(BaseConfig, LogBDDCucumberJSONProtocol):  # type: ignore[misc]
        pass

else:
    from pytest_bdd.compatibility.pytest import Config


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


def configure(config: Union[Config, "BaseConfig"]) -> None:
    cucumber_json_path = config.option.cucumber_json_path
    # prevent opening json log on worker nodes (xdist)
    if cucumber_json_path and not hasattr(config, "workerinput"):
        cast(Config, config)._bddcucumberjson = LogBDDCucumberJSON(cucumber_json_path)
        config.pluginmanager.register(cast(Config, config)._bddcucumberjson)


def unconfigure(config: Union[Config, "BaseConfig"]) -> None:
    xml = getattr(config, "_bddcucumberjson", None)
    if xml is not None:
        _config = cast(Config, config)
        del _config._bddcucumberjson
        config.pluginmanager.unregister(xml)


class ElementType(Enum):
    background = "background"
    scenario = "scenario"


class Argument(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    value: Optional[str] = None
    offset: Optional[float] = None


class Status(Enum):
    passed = "passed"
    failed = "failed"
    skipped = "skipped"
    undefined = "undefined"
    pending = "pending"
    unknown = "unknown"


class DocString(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    line: Optional[float] = None
    value: Optional[str] = None
    content_type: Optional[str] = None


class DataTableRow(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    cells: List[str]


class Tag(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    name: str
    line: Optional[float] = None


class Match(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    location: Optional[str] = None
    arguments: Optional[List["Argument"]] = None


class Result(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    duration: Optional[float] = None
    status: "Status"
    error_message: Optional[str] = None


class Step(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    keyword: Optional[str] = None
    line: Optional[float] = None
    match: Optional["Match"] = None
    name: Optional[str] = None
    result: Optional["Result"] = None
    doc_string: Optional["DocString"] = None
    rows: Optional[List["DataTableRow"]] = None


class Hook(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    match: Optional["Match"] = None
    result: "Result"


class Element(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    start_timestamp: Optional[str] = None
    line: Optional[float] = None
    id: Optional[str] = None
    type: Optional["ElementType"] = None
    keyword: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    before: Optional[List["Hook"]] = None
    steps: Optional[List["Step"]] = None
    after: Optional[List["Hook"]] = None
    tags: Optional[List["Tag"]] = None


class Feature(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    uri: Optional[str] = None
    id: Optional[str] = None
    line: Optional[float] = None
    keyword: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    elements: Optional[List["Element"]] = None
    tags: Optional[List["Tag"]] = None


class CucumberJson(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )
    implementation: Optional[str] = None
    features: Optional[List["Feature"]] = None


class LogBDDCucumberJSON:

    """Logging plugin for cucumber like json output."""

    def __init__(self, logfile: str) -> None:
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.features: Dict[str, dict] = {}

    def _get_result(self, step: Dict[str, Any], report: TestReport, error_message: bool = False) -> Dict[str, Any]:
        """Get scenario test run result.

        :param step: `StepHandler` step we get result for
        :param report: pytest `Report` object
        :return: `dict` in form {"status": "<passed|failed|skipped>", ["error_message": "<error_message>"]}
        """
        result: Dict[str, Any] = {}
        if report.passed or not step["failed"]:  # ignore setup/teardown
            result = {"status": "passed"}
        elif report.failed and step["failed"]:
            result = {"status": "failed", "error_message": str(report.longrepr) if error_message else ""}
        elif report.skipped:
            result = {"status": "skipped"}
        result["duration"] = int(math.floor((10**9) * step["duration"]))  # nanosec
        return result

    def _serialize_tags(self, item: Dict[str, Any]) -> Sequence[Dict[str, Any]]:
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

        def stepmap(step: Dict[str, Any]) -> Dict[str, Any]:
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
            for feature in self.features.values():
                Feature.model_validate(feature)
            logfile.write(json.dumps(list(self.features.values())))

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        terminalreporter.write_sep("-", f"generated json file: {self.logfile}")
