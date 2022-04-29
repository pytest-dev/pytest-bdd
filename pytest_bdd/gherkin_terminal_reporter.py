from __future__ import annotations

from typing import Any

from pytest_bdd.typing.pytest import Config, Parser, TerminalReporter, TestReport


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
                "Currently '{0}' is used."
                "Please decide to use one by deactivating {0} or gherkin-terminal-reporter.".format(
                    current_reporter.__class__
                )
            )
        gherkin_reporter = GherkinTerminalReporter(config)
        config.pluginmanager.unregister(current_reporter)
        config.pluginmanager.register(gherkin_reporter, "terminalreporter")
        if config.pluginmanager.getplugin("dsession"):
            raise Exception("gherkin-terminal-reporter is not compatible with 'xdist' plugin.")


class GherkinTerminalReporter(TerminalReporter):  # type: ignore
    def __init__(self, config: Config) -> None:
        super().__init__(config)

    def pytest_runtest_logreport(self, report: TestReport) -> Any:
        rep = report
        res = self.config.hook.pytest_report_teststatus(report=rep, config=self.config)
        cat, letter, word = res

        if not letter and not word:
            # probably passed setup/teardown
            return

        if isinstance(word, tuple):
            word, word_markup = word
        else:
            if rep.passed:
                word_markup = {"green": True}
            elif rep.failed:
                word_markup = {"red": True}
            elif rep.skipped:
                word_markup = {"yellow": True}
        scenario_markup = word_markup

        if self.verbosity <= 0 or not hasattr(report, "scenario"):
            return super().pytest_runtest_logreport(report)

        scenario = report.scenario
        self.ensure_newline()
        self._tw.write(f"Feature: {scenario['feature']['name']}\n", blue=True)
        self._tw.write(f"    Scenario: {scenario['name']}", **scenario_markup)
        if self.verbosity > 1:
            self._tw.write("\n")
            has_already_failed = False
            for step in scenario["steps"]:
                step_markup = {"red" if step["failed"] else "green": True}
                # Highlight first failed step
                if step["failed"] and not has_already_failed:
                    step_markup["bold"] = True
                    has_already_failed = True
                step_status_text = "(FAILED)" if step["failed"] else "(PASSED)"
                self._tw.write(f"        {step['keyword']} {step['name']} {step_status_text}\n", **step_markup)
        self._tw.write(f"    {word}\n", **word_markup)
        self.stats.setdefault(cat, []).append(rep)
