"""Test scenario decorator."""

import textwrap


def test_scenario_not_found(pytester, pytest_params):
    """Test the situation when scenario is not found."""
    pytester.makefile(
        ".feature",
        not_found=textwrap.dedent(
            """\
            Feature: Scenario is not found

            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import re
        import pytest
        from pytest_bdd import parsers, given, then, scenario

        @scenario("not_found.feature", "NOT FOUND")
        def test_not_found():
            pass

        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)

    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines('*Scenario "NOT FOUND" in feature "Scenario is not found" in*')


def test_scenario_comments(pytester):
    """Test comments inside scenario."""
    pytester.makefile(
        ".feature",
        comments=textwrap.dedent(
            """\
            Feature: Comments
                Scenario: Comments
                    # Comment
                    Given I have a bar

                Scenario: Strings that are not #comments
                    Given comments should be at the start of words
                    Then this is not a#comment
                    And this is not a # comment
                    And this is not "#acomment"

            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        import re
        import pytest
        from pytest_bdd import parsers, given, then, scenario

        @scenario("comments.feature", "Comments")
        def test_1():
            pass

        @scenario("comments.feature", "Strings that are not #comments")
        def test_2():
            pass


        @given("I have a bar")
        def _():
            return "bar"


        @given("comments should be at the start of words")
        def _():
            pass


        @then("this is not a#comment")
        @then("this is not a # comment")
        @then('this is not "#acomment"')
        def _():
            pass

        """
        )
    )

    result = pytester.runpytest()

    result.assert_outcomes(passed=2)


def test_scenario_not_decorator(pytester, pytest_params):
    """Test scenario function is used not as decorator."""
    pytester.makefile(
        ".feature",
        foo="""
        Feature: Test function is not a decorator
            Scenario: Foo
                Given I have a bar
        """,
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenario

        test_foo = scenario('foo.feature', 'Foo')
        """
    )

    result = pytester.runpytest_subprocess(*pytest_params)

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines("*ScenarioIsDecoratorOnly: scenario function can only be used as a decorator*")


def test_simple(pytester, pytest_params):
    """Test scenario decorator with a standard usage."""
    pytester.makefile(
        ".feature",
        simple="""
        Feature: Simple feature
            Scenario: Simple scenario
                Given I have a bar
        """,
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenario, given, then

        @scenario("simple.feature", "Simple scenario")
        def test_simple():
            pass

        @given("I have a bar")
        def _():
            return "bar"

        @then("pass")
        def _():
            pass
        """
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_angular_brackets_are_not_parsed(pytester):
    """Test that angular brackets are not parsed for "Scenario"s.

    (They should be parsed only when used in "Scenario Outline")

    """
    pytester.makefile(
        ".feature",
        simple="""
        Feature: Simple feature
            Scenario: Simple scenario
                Given I have a <tag>
                Then pass

            Scenario Outline: Outlined scenario
                Given I have a templated <foo>
                Then pass

            Examples:
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
    result = pytester.runpytest()
    result.assert_outcomes(passed=2)
