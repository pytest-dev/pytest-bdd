"""Cucumber json output formatter."""
import os
import time

import json

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
    if xml:
        del config._bddcucumberjson
        config.pluginmanager.unregister(xml)


def mangle_testnames(names):
    names = [x.replace('.py', '') for x in names if x != '()']
    names[0] = names[0].replace('/', '.')
    return names


class LogBDDCucumberJSON(object):
    """Log plugin for cucumber like json output."""

    def __init__(self, logfile):
        logfile = os.path.expanduser(os.path.expandvars(logfile))
        self.logfile = os.path.normpath(os.path.abspath(logfile))
        self.tests = {}
        self.features = {}

    # def _write_captured_output(self, report):
    #     for capname in ('out', 'err'):
    #         allcontent = ''
    #         for name, content in report.get_sections('Captured std%s' % capname):
    #             allcontent += content
    #         if allcontent:
    #             tag = getattr(Junit, 'system-'+capname)
    #             self.append(tag(bin_xml_escape(allcontent)))

    def append(self, obj):
        self.tests[-1].append(obj)

    def _get_result(self, report):
        """Get scenario test run result."""
        if report.passed:
            if report.when == 'call':  # ignore setup/teardown
                return {'status': 'passed'}
        elif report.failed:
            return {
                'status': 'failed',
                'error_message': str(report.longrepr.reprcrash) }
        elif report.skipped:
            return {'status': 'skipped'}

    def pytest_runtest_logreport(self, report):
        names = mangle_testnames(report.nodeid.split('::'))
        classnames = names[:-1]
        test_id = '.'.join(classnames)
        try:
            scenario = report.item.obj.__scenario__
        except AttributeError:
            # skip reporting for non-bdd tests
            return

        if not(scenario.steps):
            #skip if there are no steps
            return

        def stepMap(step):
            return {
                        "keyword": step.type,
                        "name": step._name,
                        "line": step.line_number,
                        "match": {
                            "location": "features/step_definitions/steps.rb:5"
                        },
                        "result": self._get_result(report)
                    }

        steps = map(stepMap, scenario.steps)

        if (not(self.tests.has_key(scenario.feature.filename))):
            self.tests[scenario.feature.filename] = {
                "keyword": "Feature",
                "name": scenario.feature.name,
                "id": scenario.feature.name.lower().replace(' ', '-'),
                "line": scenario.feature.line_number,
                "tags": [],
                "elements": []
            }

        self.tests[scenario.feature.filename].elements.add({
                "keyword": "Scenario",
                "id": test_id,
                "name": scenario.name,
                "line": scenario.line_number,
                "description": '',
                "tags": [],
                "type": "scenario",
                "steps": steps
            })


    def pytest_sessionstart(self):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self):
        if py.std.sys.version_info[0] < 3:
            logfile = py.std.codecs.open(self.logfile, 'w', encoding='utf-8')
        else:
            logfile = open(self.logfile, 'w', encoding='utf-8')

        logfile.write(json.dumps(self.tests))
        logfile.close()

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep('-', 'generated json file: %s' % (self.logfile))
