"""Test scenario decorator."""

import textwrap

from tests.utils import assert_outcomes, PYTEST_6


def test_scenario_not_found(testdir):
    """Test the situation when scenario is not found."""
    testdir.makefile(
        ".feature",
        not_found=textwrap.dedent(
            """\
            Feature: Scenario is not found

            """
        ),
    )
    testdir.makepyfile(
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
    result = testdir.runpytest()

    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines('*Scenario "NOT FOUND" in feature "Scenario is not found" in*')


def test_scenario_comments(testdir):
    """Test comments inside scenario."""
    testdir.makefile(
        ".feature",
        comments=textwrap.dedent(
            """\
            Feature: Comments
                Scenario: Comments
                    # Comment
                    Given I have a bar

                Scenario: Strings that are not comments
                    Given comments should be at the start of words
                    Then this is not a#comment
                    And this is not "#acomment"

            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
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
    )


def test_scenario_not_decorator(testdir):
    """Test scenario function is used not as decorator."""
    testdir.makefile(
        ".feature",
        foo="""
        Feature: Test function is not a decorator
            Scenario: Foo
                Given I have a bar
        """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario

        test_foo = scenario('foo.feature', 'Foo')
        """
    )

    result = testdir.runpytest()

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines("*ScenarioIsDecoratorOnly: scenario function can only be used as a decorator*")


@pytest.mark.skipif(
    not PYTEST_6,
    reason="--import-mode not supported on this pytest version",
)
@pytest.mark.parametrize('import_mode', [None, 'prepend', 'importlib', 'append'])
def test_import_mode(testdir, import_mode):
    """Test scenario function with importlib import mode."""
    testdir.makefile(
        ".feature",
        simple="""
        Feature: Simple feature
            Scenario: Simple scenario
                Given I have a bar
        """,
        many_scenarios="""
           Feature: Many scenarios
               Scenario: Scenario A
                   Given I have a bar
                   Then pass
               Scenario: Scenario B
                   Then pass
           """,
    )
    testdir.makepyfile(
        """
        from pytest_bdd import scenario, scenarios, given, then

        scenarios("many_scenarios.feature")

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
    if import_mode is None:
        params = []
    else:
        params = ['--import-mode=' + import_mode]
    result = testdir.runpytest_subprocess(*params)
    result.assert_outcomes(passed=3)
