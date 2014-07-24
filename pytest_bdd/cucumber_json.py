"""Cucumber json output formatter."""
import json
import os
import time

import py


def pytest_addoption(parser):
    group = parser.getgroup('pytest-bdd')
    group.addoption(
        '--cucumberjson', '--cucumber-json', action='store',
        dest='cucumber_json_path', metavar='path', default=None,
        help='create cucumber json style report file at given path.')


def pytest_configure(config):
    cucumber_json_path = config.option.cucumber_json_path
    # prevent opening json log on slave nodes (xdist)
    if cucumber_json_path and not hasattr(config, 'slaveinput'):
        config._bddcucumberjson = LogBDDCucumberJSON(cucumber_json_path)
        config.pluginmanager.register(config._bddcucumberjson)


def pytest_unconfigure(config):
    xml = getattr(config, '_bddcucumberjson', None)
    if xml is not None:
        del config._bddcucumberjson
        config.pluginmanager.unregister(xml)


class LogBDDCucumberJSON(object):

    """Logging plugin for cucumber like json output."""

    def __init__(self, logfile):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.features = {}

    def append(self, obj):
        self.features[-1].append(obj)

    def _get_result(self, report):
        """Get scenario test run result."""
        if report.passed:
            if report.when == 'call':  # ignore setup/teardown
                return {'status': 'passed'}
        elif report.failed:
            return {
                'status': 'failed',
                'error_message': str(report.longrepr.reprcrash),
            }
        elif report.skipped:
            return {'status': 'skipped'}

    def pytest_runtest_logreport(self, report):
        try:
            scenario = report.scenario
        except AttributeError:
            # skip reporting for non-bdd tests
            return

        if not scenario['steps'] or self._get_result(report) is None:
            # skip if there isn't a result or scenario has no steps
            return

        def stepmap(step):
            return {
                "keyword": step['type'].capitalize(),
                "name": step['name'],
                "line": step['line_number'],
                "match": {
                    "location": ""
                },
                "result": self._get_result(report),
            }

        if scenario['feature']['filename'] not in self.features:
            self.features[scenario['feature']['filename']] = {
                "keyword": "Feature",
                "uri": scenario['feature']['rel_filename'],
                "name": scenario['feature']['name'],
                "id": scenario['feature']['name'].lower().replace(' ', '-'),
                "line": scenario['feature']['line_number'],
                "description": scenario['feature']['description'],
                "tags": [],
                "elements": [],
            }

        self.features[scenario['feature']['filename']]['elements'].append({
            "keyword": "Scenario",
            "id": report.item['name'],
            "name": scenario['name'],
            "line": scenario['line_number'],
            "description": '',
            "tags": [],
            "type": "scenario",
            "steps": [stepmap(step) for step in scenario['steps']],
        })

    def pytest_sessionstart(self):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self):
        if py.std.sys.version_info[0] < 3:
            logfile_open = py.std.codecs.open
        else:
            logfile_open = open
        with logfile_open(self.logfile, 'w', encoding='utf-8') as logfile:
            logfile.write(json.dumps(list(self.features.values())))

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep('-', 'generated json file: %s' % (self.logfile))
