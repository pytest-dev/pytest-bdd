"""Test scenario decorator."""
import textwrap
import pytest

import six

from pytest_bdd import scenario, exceptions


def test_scenario_not_found(testdir):
    """Test the situation when scenario is not found."""
    feature = testdir.makefile(
        ".feature",
        not_found=textwrap.dedent(
            """\
            Feature: Scenario is not found

            """
        ),
    )

    with pytest.raises(exceptions.ScenarioNotFound) as exc_info:
        scenario(feature.strpath, "NOT FOUND")
    assert six.text_type(exc_info.value).startswith(
        'Scenario "NOT FOUND" in feature "Scenario is not found" in {feature_path}'.format(
            feature_path=feature.strpath,
        )
    )


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
