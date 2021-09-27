from _pytest.terminal import TerminalReporter


def add_options(parser):
    group = parser.getgroup("terminal reporting", "reporting", after="general")
    group._addoption(
        "--gherkin-terminal-reporter",
        action="store_true",
        dest="gherkin_terminal_reporter",
        default=False,
        help="enable gherkin output",
    )


def configure(config):
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


class GherkinTerminalReporter(TerminalReporter):
    def __init__(self, config):
        super().__init__(config)

    def pytest_runtest_logreport(self, report):
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
        feature_markup = {"blue": True}
        scenario_markup = word_markup

        if self.verbosity <= 0:
            return super().pytest_runtest_logreport(rep)
        elif self.verbosity == 1:
            if hasattr(report, "scenario"):
                self.ensure_newline()
                self._tw.write("Feature: ", **feature_markup)
                self._tw.write(report.scenario["feature"]["name"], **feature_markup)
                self._tw.write("\n")
                self._tw.write("    Scenario: ", **scenario_markup)
                self._tw.write(report.scenario["name"], **scenario_markup)
                self._tw.write(" ")
                self._tw.write(word, **word_markup)
                self._tw.write("\n")
            else:
                return super().pytest_runtest_logreport(rep)
        elif self.verbosity > 1:
            if hasattr(report, "scenario"):
                self.ensure_newline()
                self._tw.write("Feature: ", **feature_markup)
                self._tw.write(report.scenario["feature"]["name"], **feature_markup)
                self._tw.write("\n")
                self._tw.write("    Scenario: ", **scenario_markup)
                self._tw.write(report.scenario["name"], **scenario_markup)
                self._tw.write("\n")
                for step in report.scenario["steps"]:
                    self._tw.write(f"        {step['keyword']} {step['name']}\n", **scenario_markup)
                self._tw.write("    " + word, **word_markup)
                self._tw.write("\n\n")
            else:
                return super().pytest_runtest_logreport(rep)
        self.stats.setdefault(cat, []).append(rep)
