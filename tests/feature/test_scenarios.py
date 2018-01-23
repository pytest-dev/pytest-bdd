"""Test scenarios shortcut."""
import textwrap


def test_scenarios(testdir):
    """Test scenarios shortcut."""
    testdir.makeini("""
            [pytest]
            console_output_style=classic
        """)
    testdir.makeconftest("""
        import pytest
        from pytest_bdd import given

        @given('I have a bar')
        def i_have_bar():
            print('bar!')
            return 'bar'
    """)
    features = testdir.mkdir('features')
    features.join('test.feature').write_text(textwrap.dedent(u"""
    Scenario: Test scenario
        Given I have a bar
    """), 'utf-8', ensure=True)
    features.join('subfolder', 'test.feature').write_text(textwrap.dedent(u"""
    Scenario: Test subfolder scenario
        Given I have a bar

    Scenario: Test failing subfolder scenario
        Given I have a failing bar

    Scenario: Test already bound scenario
        Given I have a bar

    Scenario: Test scenario
        Given I have a bar
    """), 'utf-8', ensure=True)
    testdir.makepyfile("""
        import pytest
        from pytest_bdd import scenarios, scenario

        @scenario('features/subfolder/test.feature', 'Test already bound scenario')
        def test_already_bound():
            pass

        scenarios('features')
    """)
    result = testdir.runpytest('-v', '-s')
    result.stdout.fnmatch_lines(['*collected 5 items'])
    result.stdout.fnmatch_lines(['*test_test_subfolder_scenario *bar!', 'PASSED'])
    result.stdout.fnmatch_lines(['*test_test_scenario *bar!', 'PASSED'])
    result.stdout.fnmatch_lines(['*test_test_failing_subfolder_scenario *FAILED'])
    result.stdout.fnmatch_lines(['*test_already_bound *bar!', 'PASSED'])
    result.stdout.fnmatch_lines(['*test_test_scenario_1 *bar!', 'PASSED'])


def test_scenarios_none_found(testdir):
    """Test scenarios shortcut when no scenarios found."""
    testpath = testdir.makepyfile("""
        import pytest
        from pytest_bdd import scenarios

        scenarios('.')
    """)
    reprec = testdir.inline_run(testpath)
    reprec.assertoutcome(failed=1)
    assert 'NoScenariosFound' in str(reprec.getreports()[1].longrepr)
