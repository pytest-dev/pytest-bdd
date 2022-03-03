"""Test scenarios shortcut."""
import textwrap

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
        def i_have_bar():
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
