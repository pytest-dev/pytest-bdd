from __future__ import annotations

import typing

from _pytest.terminal import TerminalReporter

if typing.TYPE_CHECKING:
    from typing import Any

    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.reports import TestReport


def add_options(parser: Parser) -> None:
    """Add command line option to enable Gherkin terminal reporter."""
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        "--gherkin-terminal-reporter",
        action="store_true",
        dest="gherkin_terminal_reporter",
        default=False,
        help="Enable Gherkin style output for terminal reporting.",
    )


def configure(config: Config) -> None:
    """Configure the terminal reporter to use GherkinTerminalReporter if enabled."""
    if config.option.gherkin_terminal_reporter:
        current_reporter = config.pluginmanager.getplugin("terminalreporter")

        if current_reporter.__class__ != TerminalReporter:
            raise Exception(
                f"gherkin-terminal-reporter is not compatible with any other terminal reporter."
                f"Currently '{current_reporter.__class__}' is used."
                f"Please deactivate either {current_reporter.__class__} or gherkin-terminal-reporter."
            )

        gherkin_reporter = GherkinTerminalReporter(config)
        config.pluginmanager.unregister(current_reporter)
        config.pluginmanager.register(gherkin_reporter, "terminalreporter")

        if config.pluginmanager.getplugin("dsession"):
            raise Exception("gherkin-terminal-reporter is not compatible with 'xdist' plugin.")


class GherkinTerminalReporter(TerminalReporter):  # type: ignore
    def __init__(self, config: Config) -> None:
        """Initialize GherkinTerminalReporter."""
        super().__init__(config)

    def pytest_runtest_logreport(self, report: TestReport) -> Any:
        """Override log reporting to display Gherkin-style output."""
        res = self.config.hook.pytest_report_teststatus(report=report, config=self.config)
        cat, letter, word = res

        if not letter and not word:
            return None  # Passed setup/teardown

        # Determine color markup based on test outcome
        word_markup = self._get_markup_for_result(report)

        if self.verbosity <= 0 or not hasattr(report, "scenario"):
            return super().pytest_runtest_logreport(report)

        feature_markup = {"blue": True}
        scenario_markup = word_markup

        self.ensure_newline()

        if self.verbosity == 1:
            self._print_summary_report(report, word, feature_markup, scenario_markup, word_markup)
        elif self.verbosity > 1:
            self._print_detailed_report(report, word, feature_markup, scenario_markup, word_markup)

        self.stats.setdefault(cat, []).append(report)
        return None

    @staticmethod
    def _get_markup_for_result(report: TestReport) -> dict[str, bool]:
        """Get color markup based on test result."""
        if report.passed:
            return {"green": True}
        elif report.failed:
            return {"red": True}
        elif report.skipped:
            return {"yellow": True}
        return {}

    def _print_summary_report(
        self, report: TestReport, word: str, feature_markup: dict, scenario_markup: dict, word_markup: dict
    ) -> None:
        """Print a summary-style Gherkin report for a test."""
        indent = self._get_indent_for_scenario(report)

        self._tw.write(f"{report.scenario['feature']['keyword']}: ", **feature_markup)
        self._tw.write(report.scenario["feature"]["name"], **feature_markup)
        self._tw.write("\n")

        if "rule" in report.scenario:
            self._tw.write(f"    {report.scenario['rule']['keyword']}: {report.scenario['rule']['name']}\n")

        self._tw.write(f"{indent}{report.scenario['keyword']}: ", **scenario_markup)
        self._tw.write(report.scenario["name"], **scenario_markup)
        self._tw.write(f" {word}\n", **word_markup)

    def _print_detailed_report(
        self, report: TestReport, word: str, feature_markup: dict, scenario_markup: dict, word_markup: dict
    ) -> None:
        """Print a detailed Gherkin report for a test."""
        indent = self._get_indent_for_scenario(report)

        self._tw.write(f"{report.scenario['feature']['keyword']}: ", **feature_markup)
        self._tw.write(report.scenario["feature"]["name"], **feature_markup)
        self._tw.write("\n")

        if "rule" in report.scenario:
            self._tw.write(f"    {report.scenario['rule']['keyword']}: {report.scenario['rule']['name']}\n")

        self._tw.write(f"{indent}{report.scenario['keyword']}: ", **scenario_markup)
        self._tw.write(report.scenario["name"], **scenario_markup)
        self._tw.write("\n")

        for step in report.scenario["steps"]:
            self._tw.write(f"{indent}    {step['keyword']} {step['name']}\n", **scenario_markup)

        self._tw.write(f"{indent}{word}\n", **word_markup)
        self._tw.write("\n")

    @staticmethod
    def _get_indent_for_scenario(report: TestReport) -> str:
        """Get the correct indentation based on whether a rule exists."""
        if "rule" in report.scenario:
            return "        "  # Indent scenarios/examples under a rule
        return "    "  # No extra indent when there is no rule
