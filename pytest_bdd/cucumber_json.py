'''Cucumber json output formatter.'''
import os

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
        self.tests = []
        self.passed = self.skipped = 0
        self.failed = self.errors = 0

    def _opentestcase(self, report):
        names = mangle_testnames(report.nodeid.split('::'))
        classnames = names[:-1]
        if self.prefix:
            classnames.insert(0, self.prefix)
        self.tests.append(Junit.testcase(
            classname='.'.join(classnames),
            name=bin_xml_escape(names[-1]),
            time=getattr(report, 'duration', 0)
        ))

    def _write_captured_output(self, report):
        for capname in ('out', 'err'):
            allcontent = ''
            for name, content in report.get_sections('Captured std%s' % capname):
                allcontent += content
            if allcontent:
                tag = getattr(Junit, 'system-'+capname)
                self.append(tag(bin_xml_escape(allcontent)))

    def append(self, obj):
        self.tests[-1].append(obj)

    def append_pass(self, report):
        self.passed += 1
        self._write_captured_output(report)

    def append_failure(self, report):
        #msg = str(report.longrepr.reprtraceback.extraline)
        if hasattr(report, 'wasxfail'):
            self.append(
                Junit.skipped(message='xfail-marked test passes unexpectedly'))
            self.skipped += 1
        else:
            fail = Junit.failure(message='test failure')
            fail.append(bin_xml_escape(report.longrepr))
            self.append(fail)
            self.failed += 1
        self._write_captured_output(report)

    def append_collect_failure(self, report):
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.append(Junit.failure(bin_xml_escape(report.longrepr),
                                  message='collection failure'))
        self.errors += 1

    def append_collect_skipped(self, report):
        #msg = str(report.longrepr.reprtraceback.extraline)
        self.append(Junit.skipped(bin_xml_escape(report.longrepr),
                                  message='collection skipped'))
        self.skipped += 1

    def append_error(self, report):
        self.append(Junit.error(bin_xml_escape(report.longrepr),
                                message='test setup failure'))
        self.errors += 1

    def append_skipped(self, report):
        if hasattr(report, 'wasxfail'):
            self.append(Junit.skipped(bin_xml_escape(report.wasxfail),
                                      message='expected test failure'))
        else:
            filename, lineno, skipreason = report.longrepr
            if skipreason.startswith('Skipped: '):
                skipreason = bin_xml_escape(skipreason[9:])
            self.append(
                Junit.skipped(
                    '%s:%s: %s' % report.longrepr,
                    type='pytest.skip',
                    message=skipreason))
        self.skipped += 1
        self._write_captured_output(report)

    def pytest_runtest_logreport(self, report):
        if report.passed:
            if report.when == 'call':  # ignore setup/teardown
                self._opentestcase(report)
                self.append_pass(report)
        elif report.failed:
            self._opentestcase(report)
            if report.when != 'call':
                self.append_error(report)
            else:
                self.append_failure(report)
        elif report.skipped:
            self._opentestcase(report)
            self.append_skipped(report)

    def pytest_collectreport(self, report):
        if not report.passed:
            self._opentestcase(report)
            if report.failed:
                self.append_collect_failure(report)
            else:
                self.append_collect_skipped(report)

    def pytest_internalerror(self, excrepr):
        self.errors += 1
        data = bin_xml_escape(excrepr)
        self.tests.append(
            Junit.testcase(
                Junit.error(data, message='internal error'),
                classname='pytest',
                name='internal'))

    def pytest_sessionstart(self):
        self.suite_start_time = time.time()

    def pytest_sessionfinish(self):
        if py.std.sys.version_info[0] < 3:
            logfile = py.std.codecs.open(self.logfile, 'w', encoding='utf-8')
        else:
            logfile = open(self.logfile, 'w', encoding='utf-8')

        suite_stop_time = time.time()
        suite_time_delta = suite_stop_time - self.suite_start_time
        numtests = self.passed + self.failed

        logfile.write('<?xml version="1.0" encoding="utf-8"?>')
        logfile.write(Junit.testsuite(
            self.tests,
            name='pytest',
            errors=self.errors,
            failures=self.failed,
            skips=self.skipped,
            tests=numtests,
            time='%.3f' % suite_time_delta,
        ).unicode(indent=0))
        logfile.close()

    def pytest_terminal_summary(self, terminalreporter):
        terminalreporter.write_sep('-', 'generated json file: %s' % (self.logfile))
