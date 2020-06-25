"""Auto collect tests."""
import pytest

import textwrap


@pytest.fixture
def auto_collect_test_dir(testdir):
    dirname = "test_auto_collect"
    tests = testdir.mkpydir(dirname)

    tests.join("foo.feature").write(
        textwrap.dedent(
            r"""
                Feature: The feature
                Scenario: Some scenario
            """
        )
    )


def test_auto_collect_tests(auto_collect_test_dir, testdir):
    testdir.makeini(
        """
            [pytest]
            bdd_auto_collect=true
        """
    )

    result = testdir.runpytest()

    result.stdout.fnmatch_lines("collected 1 item")
    result.assert_outcomes(passed=1)


def test_auto_collect_tests_disabled(auto_collect_test_dir, testdir):
    result = testdir.runpytest()

    result.stdout.fnmatch_lines("collected 0 items")
