import re
import shutil
from functools import partial
from itertools import islice
from operator import attrgetter, itemgetter
from pathlib import Path
from typing import TYPE_CHECKING

from pytest_bdd import given, step
from pytest_bdd.compatibility.pytest import assert_outcomes
from pytest_bdd.utils import compose

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir


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

    outcome = testrunner(*options_dict.get("cli_args", []))

    yield outcome


@step("pytest outcome must contain tests with statuses:")
def check_pytest_test_statuses(pytest_result, step):
    outcomes_kwargs = map(attrgetter("value"), step.data_table.rows[0].cells)
    outcomes_kwargs_values = map(compose(int, attrgetter("value")), step.data_table.rows[1].cells)
    outcome_result = dict(zip(outcomes_kwargs, outcomes_kwargs_values))

    assert_outcomes(pytest_result, **outcome_result)


@step("pytest outcome must match lines:")
def check_pytest_stdout_lines(pytest_result, step):
    lines = list(map(compose(attrgetter("value"), itemgetter(0)), map(attrgetter("cells"), step.data_table.rows)))

    pytest_result.stdout.fnmatch_lines(lines)


@given(re.compile(r"Copy path from \"(?P<initial_path>(\w|\\|.)+)\" to test path \"(?P<final_path>(\w|\\|.)+)\""))
def copy_path(request, testdir: "Testdir", initial_path, final_path, step):
    full_initial_path = (Path(request.config.rootdir) / Path(initial_path).as_posix()).resolve(strict=True)
    full_final_path = Path(testdir.tmpdir) / Path(final_path).as_posix()
    if full_initial_path.is_file():
        full_final_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(full_initial_path, full_final_path)
    else:
        shutil.copytree(full_initial_path, full_final_path, dirs_exist_ok=True)
