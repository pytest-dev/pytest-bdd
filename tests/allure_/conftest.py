from contextlib import contextmanager
from functools import partial
from unittest import mock

import pytest
from hamcrest import all_of, any_of, assert_that, contains_string, equal_to, has_entry, has_item, has_property

from pytest_bdd import given, parsers, then, when
from pytest_bdd.typing.allure import ALLURE_INSTALLED

if ALLURE_INSTALLED:
    import allure_commons
    from allure_commons.logger import AllureFileLogger
    from allure_commons_test.report import AllureReport
    from allure_commons_test.result import has_history_id, with_status


def has_test_case(name, *matchers):
    return has_property(
        "test_cases",
        has_item(
            all_of(
                any_of(has_entry("fullName", contains_string(name)), has_entry("name", contains_string(name))),
                *matchers,
            )
        ),
    )


def has_step(name, *matchers):
    return has_entry(
        "steps", has_item(has_entry("steps", has_item(all_of(has_entry("name", equal_to(name)), *matchers))))
    )


def match(matcher, *args):
    for i, arg in enumerate(args):
        if not hasattr(arg, "__call__"):
            matcher = partial(matcher, arg)
        else:
            matcher = partial(matcher, match(arg, *args[i + 1 :]))
            break
    return matcher()


@contextmanager
def fake_logger(path, logger):
    blocked_plugins = []
    for name, plugin in allure_commons.plugin_manager.list_name_plugin():
        allure_commons.plugin_manager.unregister(plugin=plugin, name=name)
        blocked_plugins.append(plugin)

    with mock.patch(path) as ReporterMock:
        ReporterMock.return_value = logger
        yield

    for plugin in blocked_plugins:
        allure_commons.plugin_manager.register(plugin)


class AlluredTestdir:
    def __init__(self, testdir, request):
        self.testdir = testdir
        self.request = request
        self.allure_report = None

    def run_with_allure(self):
        logger = AllureFileLogger(self.testdir.tmpdir.strpath)
        with fake_logger("allure_pytest.plugin.AllureFileLogger", logger):
            self.testdir.runpytest("-s", "-v", "--alluredir", self.testdir.tmpdir)
            self.allure_report = AllureReport(self.testdir.tmpdir.strpath)


@then(parsers.re('allure report has result for (?:")(?P<scenario_name>[\\w|\\s|,]*)(?:") scenario'))
def match_scenario(allure_report, context, scenario_name):
    matcher = partial(match, has_test_case, scenario_name)
    assert_that(allure_report, matcher())
    context["scenario"] = matcher


@then(parsers.parse("this {item:w} has {status:w} status"))
def item_status(allure_report, context, item, status):
    context_matcher = context[item]
    matcher = partial(context_matcher, with_status, status)
    assert_that(allure_report, matcher())


@then(parsers.parse("this {item:w} has a history id"))
def item_history_id(allure_report, context, item):
    context_matcher = context[item]
    matcher = partial(context_matcher, has_history_id)
    assert_that(allure_report, matcher())


@then(parsers.re('this (?P<item>\\w+) contains (?:")(?P<step>[\\w|\\s|>|<]+)(?:") step'))
def step_step(allure_report, context, item, step):
    context_matcher = context[item]
    matcher = partial(context_matcher, has_step, step)
    context["step"] = matcher
    assert_that(allure_report, matcher())


@pytest.fixture
def allured_testdir(testdir, request):
    return AlluredTestdir(testdir, request)


@pytest.fixture
def context():
    return dict()


@pytest.fixture
def allure_report(allured_testdir, context):
    return allured_testdir.allure_report


@given(parsers.re("(?P<name>\\w+)(?P<extension>\\.\\w+) with content:"))
def feature_definition(name, extension, testdir, step):
    content = step.doc_string.content
    testdir.makefile(extension, **dict([(name, content)]))


@when("run pytest-bdd with allure")
def run(allured_testdir):
    allured_testdir.run_with_allure()
