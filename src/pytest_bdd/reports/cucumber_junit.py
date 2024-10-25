"""Cucumber junit output formatter."""

from __future__ import annotations

import typing
import xml.dom.minidom

from .cucumber_json import LogBDDCucumberJSON

if typing.TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.terminal import TerminalReporter

SYSTEM_OUT_DEFAULT_MESSAGE_LENGTH = 61
SYSTEM_OUT_MINIMUM_DOTS = 5
SYSTEM_OUT_INITIAL_INTEND = "      "


def add_options(parser: Parser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Cucumber JSON")
    group.addoption(
        "--cucumberjunit",
        "--cucumber-junit",
        action="store",
        dest="cucumber_junit_path",
        metavar="path",
        default=None,
        help="create cucumber junit style report file at given path.",
    )


def configure(config: Config) -> None:
    cucumber_junit_path = config.option.cucumber_junit_path
    # prevent opening junit log on worker nodes (xdist)
    if cucumber_junit_path and not hasattr(config, "workerinput"):
        config._bddcucumberjunit = LogBDDCucumberJUNIT(cucumber_junit_path)  # type: ignore[attr-defined]
        config.pluginmanager.register(config._bddcucumberjunit)  # type: ignore[attr-defined]


def unconfigure(config: Config) -> None:
    xml = getattr(config, "_bddcucumberjunit", None)  # type: ignore[attr-defined]
    if xml is not None:
        del config._bddcucumberjunit  # type: ignore[attr-defined]
        config.pluginmanager.unregister(xml)


class LogBDDCucumberJUNIT(LogBDDCucumberJSON):
    """Logging plugin for cucumber like junit output."""

    def _join_and_pad(self, str1, str2, total_length=SYSTEM_OUT_DEFAULT_MESSAGE_LENGTH):
        remaining = total_length - len(str1) - len(str2) - SYSTEM_OUT_MINIMUM_DOTS

        if remaining >= 0:
            return SYSTEM_OUT_INITIAL_INTEND + str1 + "." * (remaining + SYSTEM_OUT_MINIMUM_DOTS) + str2
        else:
            return self._join_and_pad(str1[:remaining], str2, total_length)

    def _generate_xml_report(self) -> xml.dom.minidom.Document:
        document = xml.dom.minidom.Document()

        root = document.createElement("testsuite")
        root.setAttribute("name", "pytest-bdd.cucumber.junit")
        no_of_tests = 0
        no_of_skipped = 0
        no_of_failures = 0
        no_of_errors = 0
        scenario_time = 0

        for feature in self.features.values():
            for test_case in feature["elements"]:
                no_of_tests += 1
                test_case_doc = document.createElement("testcase")
                test_case_doc.setAttribute("classname", feature["name"])
                if test_case["keyword"] == "Scenario Outline":
                    params = test_case["id"][test_case["id"].find("[") + 1 : -1]
                    name = f'{test_case["name"]} - ({params})'
                else:
                    name = test_case["name"]

                test_case_doc.setAttribute("name", name)

                failure = False
                skipped = False
                failure_doc = document.createElement("failure")
                skipped_doc = document.createElement("skipped")
                case_time = 0

                text = "\n"
                for step in test_case["steps"]:
                    text += self._join_and_pad(f'{step["keyword"]} {step["name"]}', step["result"]["status"]) + "\n"
                    case_time += step["result"]["duration"]
                    if step["result"]["status"] == "failed":
                        failure = True
                        failure_doc.appendChild(document.createTextNode(step["result"]["error_message"]))
                    elif step["result"]["status"] == "skipped":
                        skipped = True
                        skipped_doc.appendChild(document.createTextNode(step["result"]["skipped_message"]))
                test_case_doc.setAttribute("time", str(case_time))
                if failure:
                    test_case_doc.appendChild(failure_doc)
                    no_of_failures += 1
                    no_of_tests -= 1
                elif skipped:
                    test_case_doc.appendChild(skipped_doc)
                    no_of_skipped += 1
                    no_of_tests -= 1

                system_out = document.createElement("system-out")
                system_out.appendChild(document.createTextNode(text + "\n"))
                test_case_doc.appendChild(system_out)
                root.appendChild(test_case_doc)
                scenario_time += case_time

        root.setAttribute("tests", str(no_of_tests))
        root.setAttribute("skipped", str(no_of_skipped))
        root.setAttribute("failures", str(no_of_failures))
        root.setAttribute("errors", str(no_of_errors))
        root.setAttribute("time", str(scenario_time))

        document.appendChild(root)
        return document

    def pytest_sessionfinish(self) -> None:
        document = self._generate_xml_report()
        with open(self.logfile, "w", encoding="utf-8") as logfile:
            document.writexml(logfile, indent="  ", addindent="  ", newl="\n", encoding="utf-8")

    def pytest_terminal_summary(self, terminalreporter: TerminalReporter) -> None:
        terminalreporter.write_sep("-", f"generated junit file: {self.logfile}")
