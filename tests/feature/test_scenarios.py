"""Test scenarios shortcut."""

from tests.utils import assert_outcomes


def test_scenarios(testdir, pytest_params):
    """Test scenarios shortcut used together with @scenario"""
    testdir.makeini(
        # language=toml
        """\
        [pytest]
        console_output_style=classic
        """
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given('I have a bar')
        def i_have_bar():
            print('bar!')
            return 'bar'
        """
    )
    features = testdir.mkdir("features")
    features.join("test.feature").write_text(
        # language=gherkin
        """\
        Feature: Test scenarios

            Scenario: Test scenario
                Given I have a bar
        """,
        "utf-8",
        ensure=True,
    )
    features.join("subfolder", "test.feature").write_text(
        # language=gherkin
        """\
        Feature: Test scenarios
            Scenario: Test subfolder scenario
                Given I have a bar

            Scenario: Test failing subfolder scenario
                Given I have a failing bar

            Scenario: Test already bound scenario
                Given I have a bar

            Scenario: Test scenario
                Given I have a bar
        """,
        "utf-8",
        ensure=True,
    )
    testdir.makepyfile(
        # language=python
        """\
        from pathlib import Path
        from pytest_bdd import scenarios, scenario

        test_feature = scenarios('test.feature', features_base_dir=Path('features', 'subfolder'))

        @scenario('features/subfolder/test.feature', 'Test already bound scenario')
        def test_already_bound():
            pass
    """
    )
    result = testdir.runpytest("-v", "-s", *pytest_params)
    assert_outcomes(result, passed=4, failed=1)
    result.stdout.fnmatch_lines(["*collected 5 items"])
    result.stdout.fnmatch_lines(["*test*test.feature-Test scenarios-Test subfolder scenario* bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test*test.feature-Test scenarios-Test scenario* bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test*test.feature-Test scenarios-Test failing subfolder scenario* FAILED"])
    result.stdout.fnmatch_lines(["*test_already_bound* bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test*test.feature-Test scenarios-Test scenario* bar!", "PASSED"])


def test_scenarios_none_found(testdir, pytest_params):
    """Test scenarios shortcut when no scenarios found."""
    testpath = testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import scenarios

        test_feature = scenarios('.')
    """
    )
    result = testdir.runpytest_subprocess(testpath, *pytest_params)
    assert_outcomes(result, skipped=1)
