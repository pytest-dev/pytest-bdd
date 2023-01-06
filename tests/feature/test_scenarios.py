"""Test scenarios shortcut."""
from textwrap import dedent

from tests.utils import assert_outcomes


def test_scenarios(testdir, pytest_params, tmp_path):
    """Test scenarios shortcut used together with @scenario"""
    testdir.makeini(
        f"""\
        [pytest]
        console_output_style=classic
        bdd_features_base_dir={tmp_path}
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

    (tmp_path / "features" / "subfolder").mkdir(parents=True)

    (tmp_path / "features" / "test.feature").write_text(
        dedent(
            # language=gherkin
            """\
            Feature: Test scenarios

                Scenario: Test scenario
                    Given I have a bar
            """
        )
    )
    (tmp_path / "features" / "subfolder" / "test.feature").write_text(
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
        """
    )
    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import scenarios, scenario

        test_feature = scenarios('features/subfolder/test.feature')

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
