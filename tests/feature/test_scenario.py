"""Test scenario decorator."""

from tests.utils import assert_outcomes


def test_scenario_not_found(testdir, pytest_params):
    """Test the situation when scenario is not found."""
    testdir.makefile(
        ".feature",
        not_found="""\
            Feature: Scenario is not found
            """,
    )
    testdir.makepyfile(
        """\
        import re
        import pytest
        from pytest_bdd import parsers, given, then, scenario

        @scenario("not_found.feature", "NOT FOUND")
        def test_not_found():
            pass
        """
    )
    result = testdir.runpytest_subprocess(*pytest_params)

    assert_outcomes(result, skipped=1)


def test_scenario_comments(testdir):
    """Test comments inside scenario."""
    testdir.makefile(
        ".feature",
        comments="""\
            Feature: Comments
                Scenario: Comments
                    # Comment
                    Given I have a bar

                Scenario: Strings that are not comments
                    Given comments should be at the start of words
                    Then this is not a#comment
                    And this is not "#acomment"

            """,
    )

    testdir.makepyfile(
        """\
        import re
        import pytest
        from pytest_bdd import parsers, given, then, scenario

        @scenario("comments.feature", "Comments")
        def test_1():
            pass

        @scenario("comments.feature", "Strings that are not comments")
        def test_2():
            pass


        @given("I have a bar")
        def bar():
            return "bar"


        @given("comments should be at the start of words")
        def comments():
            pass


        @then(parsers.parse("this is not {acomment}"))
        def a_comment(acomment):
            assert re.search("a.*comment", acomment)
        """
    )

    result = testdir.runpytest()

    result.assert_outcomes(passed=2)


def test_simple(testdir, pytest_params):
    """Test scenario decorator with a standard usage."""
    testdir.makefile(
        ".feature",
        simple="""
        Feature: Simple feature
            Scenario: Simple scenario
                Given I have a bar
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario, given, then

        @scenario("simple.feature", "Simple scenario")
        def test_simple():
            pass

        @given("I have a bar")
        def bar():
            return "bar"

        @then("pass")
        def bar():
            pass
        """
    )
    result = testdir.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)
