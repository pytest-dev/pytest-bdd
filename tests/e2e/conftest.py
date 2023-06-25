import re
from functools import partial
from itertools import islice
from operator import attrgetter

from pytest_bdd import given, step
from pytest_bdd.compatibility.pytest import assert_outcomes
from pytest_bdd.utils import compose


@given(re.compile('File "(?P<name>\\w+)(?P<extension>\\.\\w+)" with content:'))
def write_file(name, extension, testdir, step):
    content = step.doc_string.content
    testdir.makefile(extension, **dict([(name, content)]))


@step("run pytest", target_fixture="pytest_result")
def run_pytest(testdir, step):
    if step.data_table is not None:
        data_table_keys = map(
            attrgetter("value"), map(compose(next, iter), map(attrgetter("cells"), step.data_table.rows))
        )
        data_table_values = map(
            compose(list, compose(partial(map, attrgetter("value")), lambda items: islice(items, 1, None), iter)),
            map(attrgetter("cells"), step.data_table.rows),
        )
        options_dict = dict(zip(data_table_keys, data_table_values))
    else:
        options_dict = {}
    testrunner = testdir.runpytest_inprocess if options_dict.get("subprocess", False) else testdir.runpytest

    return testrunner(*options_dict.get("cli_args", []))


@step("pytest outcome must contain tests with statuses:", target_fixture="pytest_result")
def check_pytest_outcome(pytest_result, step):
    outcomes_kwargs = map(attrgetter("value"), step.data_table.rows[0].cells)
    outcomes_kwargs_values = map(compose(int, attrgetter("value")), step.data_table.rows[1].cells)
    outcome_result = dict(zip(outcomes_kwargs, outcomes_kwargs_values))

    assert_outcomes(pytest_result, **outcome_result)
