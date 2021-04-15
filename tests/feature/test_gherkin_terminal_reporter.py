import textwrap
import pytest


FEATURE = """\
Feature: Gherkin terminal output feature
    Scenario: Scenario example 1
        Given there is a bar
        When the bar is accessed
        Then world explodes
"""

TEST = """\
from pytest_bdd import given, when, then, scenario


@given('there is a bar')
def a_bar():
    return 'bar'

@when('the bar is accessed')
def the_bar_is_accessed():
    pass


@then('world explodes')
def world_explodes():
    pass


@scenario('test.feature', 'Scenario example 1')
def test_scenario_1():
    pass

"""


def test_default_output_should_be_the_same_as_regular_terminal_reporter(testdir):
    testdir.makefile(".feature", test=FEATURE)
    testdir.makepyfile(TEST)
    regular = testdir.runpytest()
    gherkin = testdir.runpytest("--gherkin-terminal-reporter")
    regular.assert_outcomes(passed=1, failed=0)
    gherkin.assert_outcomes(passed=1, failed=0)

    def parse_lines(lines):
        return [line for line in lines if not line.startswith("===")]

    assert all(l1 == l2 for l1, l2 in zip(parse_lines(regular.stdout.lines), parse_lines(gherkin.stdout.lines)))


def test_verbose_mode_should_display_feature_and_scenario_names_instead_of_test_names_in_a_single_line(testdir):
    testdir.makefile(".feature", test=FEATURE)
    testdir.makepyfile(TEST)
    result = testdir.runpytest("--gherkin-terminal-reporter", "-v")
    result.assert_outcomes(passed=1, failed=0)
    result.stdout.fnmatch_lines("Feature: Gherkin terminal output feature")
    result.stdout.fnmatch_lines("*Scenario: Scenario example 1 PASSED")


def test_verbose_mode_should_preserve_displaying_regular_tests_as_usual(testdir):
    testdir.makepyfile(
        textwrap.dedent(
            """\
        def test_1():
            pass
        """
        )
    )
    regular = testdir.runpytest()
    gherkin = testdir.runpytest("--gherkin-terminal-reporter", "-v")
    regular.assert_outcomes(passed=1, failed=0)
    gherkin.assert_outcomes(passed=1, failed=0)

    regular.stdout.fnmatch_lines("test_verbose_mode_should_preserve_displaying_regular_tests_as_usual.py . [100%]")
    gherkin.stdout.fnmatch_lines(
        "test_verbose_mode_should_preserve_displaying_regular_tests_as_usual.py::test_1 PASSED [100%]"
    )


def test_double_verbose_mode_should_display_full_scenario_description(testdir):
    testdir.makefile(".feature", test=FEATURE)
    testdir.makepyfile(TEST)
    result = testdir.runpytest("--gherkin-terminal-reporter", "-vv")
    result.assert_outcomes(passed=1, failed=0)

    result.stdout.fnmatch_lines("*Scenario: Scenario example 1")
    result.stdout.fnmatch_lines("*Given there is a bar")
    result.stdout.fnmatch_lines("*When the bar is accessed")
    result.stdout.fnmatch_lines("*Then world explodes")
    result.stdout.fnmatch_lines("*PASSED")


@pytest.mark.parametrize("verbosity", ["", "-v", "-vv"])
def test_error_message_for_missing_steps(testdir, verbosity):
    testdir.makefile(".feature", test=FEATURE)
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenarios

        scenarios('.')
        """
        )
    )
    result = testdir.runpytest("--gherkin-terminal-reporter", verbosity)
    result.assert_outcomes(passed=0, failed=1)
    result.stdout.fnmatch_lines(
        """*StepDefinitionNotFoundError: Step definition is not found: Given "there is a bar". """
        """Line 3 in scenario "Scenario example 1"*"""
    )


@pytest.mark.parametrize("verbosity", ["", "-v", "-vv"])
def test_error_message_should_be_displayed(testdir, verbosity):
    testdir.makefile(".feature", test=FEATURE)
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, scenario


        @given('there is a bar')
        def a_bar():
            return 'bar'

        @when('the bar is accessed')
        def the_bar_is_accessed():
            pass


        @then('world explodes')
        def world_explodes():
            raise Exception("BIGBADABOOM")


        @scenario('test.feature', 'Scenario example 1')
        def test_scenario_1():
            pass
        """
        )
    )
    result = testdir.runpytest("--gherkin-terminal-reporter", verbosity)
    result.assert_outcomes(passed=0, failed=1)
    result.stdout.fnmatch_lines("E       Exception: BIGBADABOOM")
    result.stdout.fnmatch_lines("test_error_message_should_be_displayed.py:15: Exception")


def test_local_variables_should_be_displayed_when_showlocals_option_is_used(testdir):
    testdir.makefile(".feature", test=FEATURE)
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, scenario


        @given('there is a bar')
        def a_bar():
            return 'bar'

        @when('the bar is accessed')
        def the_bar_is_accessed():
            pass


        @then('world explodes')
        def world_explodes():
            local_var = "MULTIPASS"
            raise Exception("BIGBADABOOM")


        @scenario('test.feature', 'Scenario example 1')
        def test_scenario_1():
            pass
        """
        )
    )
    result = testdir.runpytest("--gherkin-terminal-reporter", "--showlocals")
    result.assert_outcomes(passed=0, failed=1)
    result.stdout.fnmatch_lines("""request*=*<FixtureRequest for *""")
    result.stdout.fnmatch_lines("""local_var*=*MULTIPASS*""")


def test_step_parameters_should_be_replaced_by_their_values(testdir):
    example = {"start": 10, "eat": 3, "left": 7}
    testdir.makefile(
        ".feature",
        test=textwrap.dedent(
            """\
        Feature: Gherkin terminal output feature
            Scenario Outline: Scenario example 2
                Given there are <start> cucumbers
                When I eat <eat> cucumbers
                Then I should have <left> cucumbers

            Examples:
            | start | eat | left |
            |{start}|{eat}|{left}|
        """.format(
                **example
            )
        ),
    )
    testdir.makepyfile(
        test_gherkin=textwrap.dedent(
            """\
            from pytest_bdd import given, when, scenario, then

            @given('there are <start> cucumbers', target_fixture="start_cucumbers")
            def start_cucumbers(start):
                return start

            @when('I eat <eat> cucumbers')
            def eat_cucumbers(start_cucumbers, eat):
                pass

            @then('I should have <left> cucumbers')
            def should_have_left_cucumbers(start_cucumbers, start, eat, left):
                pass

            @scenario('test.feature', 'Scenario example 2')
            def test_scenario_2():
                pass
        """
        )
    )

    result = testdir.runpytest("--gherkin-terminal-reporter", "--gherkin-terminal-reporter-expanded", "-vv")
    result.assert_outcomes(passed=1, failed=0)
    result.stdout.fnmatch_lines("*Scenario: Scenario example 2")
    result.stdout.fnmatch_lines("*Given there are {start} cucumbers".format(**example))
    result.stdout.fnmatch_lines("*When I eat {eat} cucumbers".format(**example))
    result.stdout.fnmatch_lines("*Then I should have {left} cucumbers".format(**example))
    result.stdout.fnmatch_lines("*PASSED")
