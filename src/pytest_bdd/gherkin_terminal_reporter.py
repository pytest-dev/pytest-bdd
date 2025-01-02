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
                f"Currently '{current_reporter.__class__}' is used."
                f"Please decide to use one by deactivating {current_reporter.__class__} "
                "or gherkin-terminal-reporter."
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
        rep = report
        res = self.config.hook.pytest_report_teststatus(report=rep, config=self.config)
        cat, letter, word = res

        if not letter and not word:
            # probably passed setup/teardown
            return None

        if isinstance(word, tuple):
            word, word_markup = word
        elif rep.passed:
            word_markup = {"green": True}
        elif rep.failed:
            word_markup = {"red": True}
        elif rep.skipped:
            word_markup = {"yellow": True}
        feature_markup = {"blue": True}
        scenario_markup = word_markup
        rule_markup = {"purple": True}

        try:
            scenario = test_report_context_registry[report].scenario
        except KeyError:
            scenario = None

        if self.verbosity <= 0 or scenario is None:
            return super().pytest_runtest_logreport(rep)

        rule = scenario.get("rule")
        indent = "    " if rule else ""

        if self.verbosity == 1:
            self.ensure_newline()
            self._tw.write(f"{scenario['feature']['keyword']}: ", **feature_markup)
            self._tw.write(scenario["feature"]["name"], **feature_markup)
            self._tw.write("\n")

            if rule and rule["name"] != self.current_rule:
                self._tw.write(f"  {rule['keyword']}: ", **rule_markup)
                self._tw.write(rule["name"], **rule_markup)
                self._tw.write("\n")
                self.current_rule = rule["name"]

            self._tw.write(f"{indent}    {scenario['keyword']}: ", **scenario_markup)
            self._tw.write(scenario["name"], **scenario_markup)
            self._tw.write(" ")
            self._tw.write(word, **word_markup)
            self._tw.write("\n")
        elif self.verbosity > 1:
            self.ensure_newline()
            self._tw.write(f"{scenario['feature']['keyword']}: ", **feature_markup)
            self._tw.write(scenario["feature"]["name"], **feature_markup)
            self._tw.write("\n")

            if rule and rule["name"] != self.current_rule:
                self._tw.write(f"  {rule['keyword']}: ", **rule_markup)
                self._tw.write(rule["name"], **rule_markup)
                self._tw.write("\n")
                self.current_rule = rule["name"]

            self._tw.write(f"{indent}    {scenario['keyword']}: ", **scenario_markup)
            self._tw.write(scenario["name"], **scenario_markup)
            self._tw.write("\n")
            for step in scenario["steps"]:
                self._tw.write(f"{indent}        {step['keyword']} {step['name']}\n", **scenario_markup)
            self._tw.write(f"{indent}    {word}", **word_markup)
            self._tw.write("\n\n")

        self.stats.setdefault(cat, []).append(rep)
