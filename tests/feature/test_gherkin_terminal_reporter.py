from __future__ import annotations

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
def _():
    return 'bar'

@when('the bar is accessed')
def _():
    pass


@then('world explodes')
def _():
    pass


@scenario('test.feature', 'Scenario example 1')
def test_scenario_1():
    pass

"""


def test_default_output_should_be_the_same_as_regular_terminal_reporter(pytester):
    pytester.makefile(".feature", test=FEATURE)
    pytester.makepyfile(TEST)
    regular = pytester.runpytest()
    gherkin = pytester.runpytest("--gherkin-terminal-reporter")
    regular.assert_outcomes(passed=1, failed=0)
    gherkin.assert_outcomes(passed=1, failed=0)

    def parse_lines(lines: list[str]) -> list[str]:
        return [line for line in lines if not line.startswith("===")]

    assert all(l1 == l2 for l1, l2 in zip(parse_lines(regular.stdout.lines), parse_lines(gherkin.stdout.lines)))


def test_verbose_mode_should_display_feature_and_scenario_names_instead_of_test_names_in_a_single_line(pytester):
    pytester.makefile(".feature", test=FEATURE)
    pytester.makepyfile(TEST)
    result = pytester.runpytest("--gherkin-terminal-reporter", "-v")
    result.assert_outcomes(passed=1, failed=0)
    result.stdout.fnmatch_lines("Feature: Gherkin terminal output feature")
    result.stdout.fnmatch_lines("*Scenario: Scenario example 1 PASSED")


def test_verbose_mode_should_preserve_displaying_regular_tests_as_usual(pytester):
    pytester.makepyfile(
        textwrap.dedent(
            """\
        def test_1():
            pass
        """
        )
    )
    regular = pytester.runpytest()
    gherkin = pytester.runpytest("--gherkin-terminal-reporter", "-v")
    regular.assert_outcomes(passed=1, failed=0)
    gherkin.assert_outcomes(passed=1, failed=0)

    regular.stdout.re_match_lines(
        r"test_verbose_mode_should_preserve_displaying_regular_tests_as_usual\.py \.\s+\[100%\]"
    )
    gherkin.stdout.re_match_lines(
        r"test_verbose_mode_should_preserve_displaying_regular_tests_as_usual\.py::test_1 PASSED\s+\[100%\]"
    )


def test_double_verbose_mode_should_display_full_scenario_description(pytester):
    pytester.makefile(".feature", test=FEATURE)
    pytester.makepyfile(TEST)
    result = pytester.runpytest("--gherkin-terminal-reporter", "-vv")
    result.assert_outcomes(passed=1, failed=0)

    result.stdout.fnmatch_lines("*Scenario: Scenario example 1")
    result.stdout.fnmatch_lines("*Given there is a bar")
    result.stdout.fnmatch_lines("*When the bar is accessed")
    result.stdout.fnmatch_lines("*Then world explodes")
    result.stdout.fnmatch_lines("*PASSED")


@pytest.mark.parametrize("verbosity", ["", "-v", "-vv"])
def test_error_message_for_missing_steps(pytester, verbosity):
    pytester.makefile(".feature", test=FEATURE)
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenarios

        scenarios('.')
        """
        )
    )
    result = pytester.runpytest("--gherkin-terminal-reporter", verbosity)
    result.assert_outcomes(passed=0, failed=1)
    result.stdout.fnmatch_lines(
        """*StepDefinitionNotFoundError: Step definition is not found: Given "there is a bar". """
        """Line 3 in scenario "Scenario example 1"*"""
    )


@pytest.mark.parametrize("verbosity", ["", "-v", "-vv"])
def test_error_message_should_be_displayed(pytester, verbosity):
    pytester.makefile(".feature", test=FEATURE)
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, scenario


        @given('there is a bar')
        def _():
            return 'bar'

        @when('the bar is accessed')
        def _():
            pass


        @then('world explodes')
        def _():
            raise Exception("BIGBADABOOM")


        @scenario('test.feature', 'Scenario example 1')
        def test_scenario_1():
            pass
        """
        )
    )
    result = pytester.runpytest("--gherkin-terminal-reporter", verbosity)
    result.assert_outcomes(passed=0, failed=1)
    result.stdout.fnmatch_lines("E       Exception: BIGBADABOOM")
    result.stdout.fnmatch_lines("test_error_message_should_be_displayed.py:15: Exception")


def test_local_variables_should_be_displayed_when_showlocals_option_is_used(pytester):
    pytester.makefile(".feature", test=FEATURE)
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, scenario


        @given('there is a bar')
        def _():
            return 'bar'

        @when('the bar is accessed')
        def _():
            pass


        @then('world explodes')
        def _():
            local_var = "MULTIPASS"
            raise Exception("BIGBADABOOM")


        @scenario('test.feature', 'Scenario example 1')
        def test_scenario_1():
            pass
        """
        )
    )
    result = pytester.runpytest("--gherkin-terminal-reporter", "--showlocals")
    result.assert_outcomes(passed=0, failed=1)
    result.stdout.fnmatch_lines("""request*=*<FixtureRequest for *""")
    result.stdout.fnmatch_lines("""local_var*=*MULTIPASS*""")


def test_step_parameters_should_be_replaced_by_their_values(pytester):
    example = {"start": 10, "eat": 3, "left": 7}
    pytester.makefile(
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
        """.format(**example)
        ),
    )
    pytester.makepyfile(
        test_gherkin=textwrap.dedent(
            """\
            from pytest_bdd import given, when, scenario, then, parsers

            @given(parsers.parse('there are {start} cucumbers'), target_fixture="start_cucumbers")
            def _(start):
                return start

            @when(parsers.parse('I eat {eat} cucumbers'))
            def _(start_cucumbers, eat):
                pass

            @then(parsers.parse('I should have {left} cucumbers'))
            def _(start_cucumbers, left):
                pass

            @scenario('test.feature', 'Scenario example 2')
            def test_scenario_2():
                pass
        """
        )
    )

    result = pytester.runpytest("--gherkin-terminal-reporter", "-vv")
    result.assert_outcomes(passed=1, failed=0)
    result.stdout.fnmatch_lines("*Scenario Outline: Scenario example 2")
    result.stdout.fnmatch_lines("*Given there are {start} cucumbers".format(**example))
    result.stdout.fnmatch_lines("*When I eat {eat} cucumbers".format(**example))
    result.stdout.fnmatch_lines("*Then I should have {left} cucumbers".format(**example))
    result.stdout.fnmatch_lines("*PASSED")


def test_scenario_alias_keywords_are_accepted(pytester):
    """
    Test that aliases for various keywords are accepted and reported correctly.
    see https://cucumber.io/docs/gherkin/reference/
    """
    pytester.makefile(
        ".feature",
        simple="""
        Feature: Simple feature
            Scenario: Simple scenario
                Given I have a <tag>
                Then pass

            Example: Simple example
                Given I have a <tag>
                Then pass

            Scenario Outline: Outlined scenario
                Given I have a templated <foo>
                Then pass

            Examples:
                | foo |
                | bar |

            Scenario Template: Templated scenario
                Given I have a templated <foo>
                Then pass

            Scenarios:
                | foo |
                | bar |
        """,
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios, given, then, parsers

        scenarios("simple.feature")

        @given("I have a <tag>")
        def _():
            return "tag"

        @given(parsers.parse("I have a templated {foo}"))
        def _(foo):
            return "foo"

        @then("pass")
        def _():
            pass
        """
    )
    result = pytester.runpytest("--gherkin-terminal-reporter", "-vv")
    result.assert_outcomes(passed=4, failed=0)
    result.stdout.fnmatch_lines("*Feature: Simple feature*")
    result.stdout.fnmatch_lines("*Example: Simple example*")
    result.stdout.fnmatch_lines("*Scenario: Simple scenario*")
    result.stdout.fnmatch_lines("*Scenario Outline: Outlined scenario*")


def test_rule_example_format_uses_correct_keywords(pytester):
    pytester.makefile(
        ".feature",
        test=textwrap.dedent(
            """\
        Feature: Gherkin terminal output with rules and examples
            Rule: Rule 1
                Example: Example 1
                    Given this is a step
                    When this is a step
                    Then this is a step
                Scenario: Scenario 2
                    Given this is a step
                    When this is a step
                    Then this is a step
            Rule: Rule 2
                Example: Example 3
                    Given this is a step
                    When this is a step
                    Then this is a step
        """
        ),
    )
    pytester.makepyfile(
        test_gherkin=textwrap.dedent(
            """\
            from pytest_bdd import step, scenarios

            @step("this is a step")
            def _():
                pass

            scenarios('test.feature')
        """
        )
    )

    result = pytester.runpytest("--gherkin-terminal-reporter", "-v")
    result.assert_outcomes(passed=3, failed=0)
    result.stdout.fnmatch_lines("*Feature: Gherkin terminal output with rules and examples*")
    result.stdout.fnmatch_lines("*Rule: Rule 1*")
    result.stdout.fnmatch_lines("*Example: Example 1*")
    result.stdout.fnmatch_lines("*Scenario: Scenario 2*")
    result.stdout.fnmatch_lines("*Rule: Rule 2*")
    result.stdout.fnmatch_lines("*Example: Example 3*")

    result = pytester.runpytest("--gherkin-terminal-reporter", "-vv")
    result.assert_outcomes(passed=3, failed=0)
    result.stdout.fnmatch_lines("*Feature: Gherkin terminal output with rules and examples*")
    result.stdout.fnmatch_lines("*Rule: Rule 1*")
    result.stdout.fnmatch_lines("*Example: Example 1*")
    result.stdout.fnmatch_lines("*Scenario: Scenario 2*")
    result.stdout.fnmatch_lines("*Rule: Rule 2*")
    result.stdout.fnmatch_lines("*Example: Example 3*")
