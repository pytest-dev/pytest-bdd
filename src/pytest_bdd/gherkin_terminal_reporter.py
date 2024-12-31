from __future__ import annotations

import typing

from _pytest.terminal import TerminalReporter

from .reporting import test_report_context_registry

if typing.TYPE_CHECKING:
    from _pytest.config import Config
    from _pytest.config.argparsing import Parser
    from _pytest.reports import TestReport


def add_options(parser: Parser) -> None:
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        "--gherkin-terminal-reporter",
        action="store_true",
        dest="gherkin_terminal_reporter",
        default=False,
        help="enable gherkin output",
    )


def configure(config: Config) -> None:
    if config.option.gherkin_terminal_reporter:
        # Get the standard terminal reporter plugin and replace it with our
        current_reporter = config.pluginmanager.getplugin("terminalreporter")
        if current_reporter.__class__ != TerminalReporter:
            raise Exception(
                "gherkin-terminal-reporter is not compatible with any other terminal reporter."
                "You can use only one terminal reporter."
                f" Currently '{current_reporter.__class__}' is used."
                f" Please decide to use one by deactivating {current_reporter.__class__} or gherkin-terminal-reporter."
            )
        gherkin_reporter = GherkinTerminalReporter(config)
        config.pluginmanager.unregister(current_reporter)
        config.pluginmanager.register(gherkin_reporter, "terminalreporter")
        if config.pluginmanager.getplugin("dsession"):
            raise Exception("gherkin-terminal-reporter is not compatible with 'xdist' plugin.")


class GherkinTerminalReporter(TerminalReporter):  # type: ignore[misc]
    def __init__(self, config: Config) -> None:
        super().__init__(config)
        self.current_rule: str | None = None

    def pytest_runtest_logreport(self, report: TestReport) -> None:
        result = self.config.hook.pytest_report_teststatus(report=report, config=self.config)
        result_category, result_letter, result_word = result

        if not result_letter and not result_word:
            return None

        try:
            scenario = test_report_context_registry[report].scenario
        except KeyError:
            scenario = None

        if self.verbosity <= 0 or scenario is None:
            return super().pytest_runtest_logreport(report)

        report_renderer = ReportRenderer(self, report, scenario, result_word)

        if self.verbosity == 1:
            report_renderer.write_scenario_summary()
        elif self.verbosity > 1:
            report_renderer.write_detailed_scenario_with_steps()

        self.stats.setdefault(result_category, []).append(report)


class ReportRenderer:
    def __init__(
        self, reporter: GherkinTerminalReporter, report: TestReport, scenario: dict, result_outcome: str
    ) -> None:
        self.reporter = reporter
        self.report = report
        self.scenario = scenario
        self.rule = scenario.get("rule")
        if isinstance(result_outcome, tuple):
            self.result_outcome, self.feature_markup = result_outcome
        else:
            self.result_outcome = result_outcome
            self.feature_markup = {"blue": True}
        self.rule_markup = {"purple": True}
        self.tw = self.reporter._tw
        self.current_indentation_index = 0

    def get_outcome_markup(self) -> dict:
        if self.report.passed:
            return {"green": True}
        elif self.report.failed:
            return {"red": True}
        elif self.report.skipped:
            return {"yellow": True}

    def write_scenario_summary(self, has_steps: bool = False) -> None:
        """Write the feature and scenario header to the terminal."""
        self.tw.write("\n")
        self.tw.write(f"{self.scenario['feature']['keyword']}: ", **self.feature_markup)
        self.tw.write(self.scenario["feature"]["name"], **self.feature_markup)
        self.tw.write("\n")

        if self.rule and self.rule["name"] != self.reporter.current_rule:
            self.current_indentation_index = 1
            self.tw.write(
                f"{self._get_indent(self.current_indentation_index)}{self.rule['keyword']}: ", **self.rule_markup
            )
            self.tw.write(self.rule["name"], **self.rule_markup)
            self.tw.write("\n")
            self.reporter.current_rule = self.rule["name"]

        self.current_indentation_index += 1
        self.tw.write(
            f"{self._get_indent(self.current_indentation_index)}{self.scenario['keyword']}: ",
            **self.get_outcome_markup(),
        )
        self.tw.write(self.scenario["name"], **self.get_outcome_markup())
        if not has_steps:
            self.tw.write(" ", **self.get_outcome_markup())
            self.tw.write(self.result_outcome, **self.get_outcome_markup())
        self.tw.write("\n")

    def write_detailed_scenario_with_steps(self) -> None:
        """Write the full details of the scenario including the steps."""
        self.write_scenario_summary(has_steps=True)

        for step in self.scenario["steps"]:
            self.current_indentation_index += 1
            self.tw.write(
                f"{self._get_indent(self.current_indentation_index)}{step['keyword']} {step['name']}\n",
                **self.get_outcome_markup(),
            )

        self.tw.write(f"{self._get_indent(2)}{self.result_outcome}", **self.get_outcome_markup())
        self.tw.write("\n\n")

    @staticmethod
    def _get_indent(level: int) -> str:
        return "    " * level
