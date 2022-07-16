"""Test scenarios shortcut."""
import textwrap

from pytest_bdd.utils import collect_dumped_objects
from tests.utils import assert_outcomes


def test_scenarios(testdir, pytest_params):
    """Test scenarios shortcut (used together with @scenario for individual test override)."""
    testdir.makeini(
        """
            [pytest]
            console_output_style=classic
        """
    )
    testdir.makeconftest(
        """
        import pytest
        from pytest_bdd import given

        @given('I have a bar')
        def _():
            print('bar!')
            return 'bar'
    """
    )
    features = testdir.mkdir("features")
    features.join("test.feature").write_text(
        textwrap.dedent(
            """
    Scenario: Test scenario
        Given I have a bar
    """
        ),
        "utf-8",
        ensure=True,
    )
    features.join("subfolder", "test.feature").write_text(
        textwrap.dedent(
            """
    Scenario: Test subfolder scenario
        Given I have a bar

    Scenario: Test failing subfolder scenario
        Given I have a failing bar

    Scenario: Test already bound scenario
        Given I have a bar

    Scenario: Test scenario
        Given I have a bar
    """
        ),
        "utf-8",
        ensure=True,
    )
    testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import scenarios, scenario

        @scenario('features/subfolder/test.feature', 'Test already bound scenario')
        def test_already_bound():
            pass

        scenarios('features')
    """
    )
    result = testdir.runpytest_subprocess("-v", "-s", *pytest_params)
    assert_outcomes(result, passed=4, failed=1)
    result.stdout.fnmatch_lines(["*collected 5 items"])
    result.stdout.fnmatch_lines(["*test_test_subfolder_scenario *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_failing_subfolder_scenario *FAILED"])
    result.stdout.fnmatch_lines(["*test_already_bound *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario_1 *bar!", "PASSED"])


def test_scenarios_none_found(testdir, pytest_params):
    """Test scenarios shortcut when no scenarios found."""
    testpath = testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import scenarios

        scenarios('.')
    """
    )
    result = testdir.runpytest_subprocess(testpath, *pytest_params)
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(["*NoScenariosFound*"])


def test_scenarios_override_caller_locals(testdir):
    testdir.makefile(
        ".feature",
        override_caller_locals=textwrap.dedent(
            """\
            Feature: @scenarios(...) decorator allow overriding caller_locals
                Scenario: I make my own scenario decorator that extends the original one
                    Given pass
                    When I dump the content of my_features_registry
                    Then pass
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import sys

        import pytest
        from pytest_bdd import given, when, then, scenarios, parsers
        from pytest_bdd.utils import dump_obj

        my_features_registry = []


        def my_scenarios(*feature_paths: str, **kwargs) -> None:
            my_features_registry.extend(feature_paths)

            scenarios(*feature_paths, **kwargs, caller_locals=sys._getframe(1).f_locals)


        my_scenarios("override_caller_locals.feature")


        @given("pass")
        @then("pass")
        def _():
            pass


        @when("I dump the content of my_features_registry")
        def _():
            dump_obj(my_features_registry)

        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    [my_features_registry] = collect_dumped_objects(result)
    assert my_features_registry == ["override_caller_locals.feature"]
