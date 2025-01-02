"""Test scenarios shortcut."""

from __future__ import annotations

import textwrap


def test_scenarios(pytester, pytest_params):
    """Test scenarios shortcut (used together with @scenario for individual test override)."""
    pytester.makeini(
        """
            [pytest]
            console_output_style=classic
        """
    )
    pytester.makeconftest(
        """
        import pytest
        from pytest_bdd import given

        @given('I have a bar')
        def _():
            print('bar!')
            return 'bar'
    """
    )
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
Feature: Test scenarios
    Scenario: Test scenario
        Given I have a bar
    """
        ),
        "utf-8",
    )
    subfolder = features.joinpath("subfolder")
    subfolder.mkdir()
    subfolder.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
Feature: Test scenarios
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
    )
    pytester.makepyfile(
        """
        import pytest
        from pytest_bdd import scenarios, scenario

        @scenario('features/subfolder/test.feature', 'Test already bound scenario')
        def test_already_bound():
            pass

        scenarios('features')
    """
    )
    result = pytester.runpytest_subprocess("-v", "-s", *pytest_params)
    result.assert_outcomes(passed=4, failed=1)
    result.stdout.fnmatch_lines(["*collected 5 items"])
    result.stdout.fnmatch_lines(["*test_test_subfolder_scenario *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_failing_subfolder_scenario *FAILED"])
    result.stdout.fnmatch_lines(["*test_already_bound *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario_1 *bar!", "PASSED"])


def test_scenarios_none_found(pytester, pytest_params):
    """Test scenarios shortcut when no scenarios found."""
    testpath = pytester.makepyfile(
        """
        import pytest
        from pytest_bdd import scenarios

        scenarios('.')
    """
    )
    result = pytester.runpytest_subprocess(testpath, *pytest_params)
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*NoScenariosFound*"])
