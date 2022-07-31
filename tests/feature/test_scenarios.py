"""Test scenarios shortcut."""
import textwrap

from pytest_bdd.utils import collect_dumped_objects


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
    result.assert_outcomes(passed=4, failed=1)
    result.stdout.fnmatch_lines(["*collected 5 items"])
    result.stdout.fnmatch_lines(["*test_test_subfolder_scenario *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_failing_subfolder_scenario *FAILED"])
    result.stdout.fnmatch_lines(["*test_already_bound *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario_1 *bar!", "PASSED"])


def test_scenarios_class(testdir):
    testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import given, scenario_class
        from pytest_bdd.utils import dump_obj

        @given('I have a bar')
        def _():
            dump_obj('bar')
            return 'bar'


        @given('I have a foo')
        def _():
            dump_obj('foo')
            return 'foo'


        TestMyFeature = scenario_class("my_feature.feature", name="TestMyFeature")
    """
    )

    testdir.makefile(
        "feature",
        my_feature="""\
            Feature: Test feature
                Scenario: Scenario foo
                    Given I have a foo
                Scenario: Scenario bar
                    Given I have a bar
            """,
    )

    result = testdir.runpytest("-s", "-v", "-o", "console_output_style=classic")
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(["*TestMyFeature::test_scenario_bar*", "PASSED"])
    result.stdout.fnmatch_lines(["*TestMyFeature::test_scenario_foo*", "PASSED"])
    objs = collect_dumped_objects(result)
    assert objs == ["bar", "foo"]


def test_scenarios_class_can_override_generated_tests(testdir):
    testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import given, scenario_class, parsers, scenario
        from pytest_bdd.utils import dump_obj

        @given(parsers.parse('I have a {value}'))
        def _(value: str) -> str:
            dump_obj(f"Given I have a {value}")
            return value


        class TestMyFeature(scenario_class("my_feature.feature")):
            # TODO: We should not be required to use @staticmethod here
            @staticmethod
            # TODO: We should not be required to pass "my_feature.feature" here
            @scenario("my_feature.feature", "Scenario foo")
            def test_my_scenario_foo():
                dump_obj("overriding scenario foo")

            @pytest.mark.skip(reason="testing marker")
            # TODO: We should not be required to use @staticmethod here
            @staticmethod
            @scenario("my_feature.feature", "Scenario bar")
            def test_my_scenario_bar_skipped():
                dump_obj("this should not be executed")
    """
    )

    testdir.makefile(
        "feature",
        my_feature="""\
            Feature: Test feature
                Scenario: Scenario bar
                    Given I have a bar
                Scenario: Scenario foo
                    Given I have a foo
                Scenario: Scenario baz
                    Given I have a baz
            """,
    )

    result = testdir.runpytest("-s", "-v", "-o", "console_output_style=classic")
    result.assert_outcomes(passed=2, skipped=1)
    result.stdout.fnmatch_lines(["*TestMyFeature::test_my_scenario_foo*", "PASSED"])
    result.stdout.fnmatch_lines(["*TestMyFeature::test_my_scenario_bar_skipped*", "SKIPPED"])
    result.stdout.fnmatch_lines(["*TestMyFeature::test_scenario_baz*", "PASSED"])
    [skip_msgs] = collect_dumped_objects(result)
    assert skip_msgs == ["overriding scenario foo", "Given I have a baz"]


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
    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines(["*NoScenariosFound*"])
