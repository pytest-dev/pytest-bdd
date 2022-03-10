"""Scenario Outline tests."""
import textwrap

from pytest_bdd.utils import collect_dumped_objects
from tests.utils import assert_outcomes

STEPS = """\
from pytest_bdd import parsers, given, when, then
from pytest_bdd.utils import dump_obj


@given(parsers.parse("there are {start:d} cucumbers"), target_fixture="cucumbers")
def given_cucumbers(start):
    assert isinstance(start, int)
    dump_obj(start)
    return {"start": start}


@when(parsers.parse("I eat {eat:g} cucumbers"))
def eat_cucumbers(cucumbers, eat):
    assert isinstance(eat, float)
    dump_obj(eat)
    cucumbers["eat"] = eat


@then(parsers.parse("I should have {left} cucumbers"))
def should_have_left_cucumbers(cucumbers, left):
    assert isinstance(left, str)
    dump_obj(left)
    assert cucumbers["start"] - cucumbers["eat"] == int(left)

"""


def test_outlined(testdir):
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined given, when, thens
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   | # a comment
                    |  5    |  4  |  1   |

            """
        ),
    )

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
        )
        def test_outline(request):
            pass

        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)
    # fmt: off
    assert collect_dumped_objects(result) == [
        12, 5.0, "7",
        5, 4.0, "1",
    ]
    # fmt: on


def test_unused_params(testdir):
    """Test parametrized scenario when the test function lacks parameters."""

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with unused params
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    # And commented out step with <unused_param>
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left | unused_param |
                    |  12   |  5  |  7   | value        |

            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with unused params")
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, passed=1)


def test_outlined_with_other_fixtures(testdir):
    """Test outlined scenario also using other parametrized fixture."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined given, when, thens
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   |
                    |  5    |  4  |  1   |

            """
        ),
    )

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import scenario


        @pytest.fixture(params=[1, 2, 3])
        def other_fixture(request):
            return request.param


        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
        )
        def test_outline(other_fixture):
            pass

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=6)


def test_outline_with_escaped_pipes(testdir):
    """Test parametrized feature example table with escaped pipe characters in input."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            r"""
            Feature: Outline With Special characters

                Scenario Outline: Outline with escaped pipe character
                    # Just print the string so that we can assert later what it was by reading the output
                    Given I print the <string>

                    Examples:
                    | string       |
                    | bork         |
                    | \|bork       |
                    | bork \|      |
                    | bork\|\|bork |
                    | \|           |
                    | bork      \\ |
                    | bork    \\\| |
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import scenario, given, parsers
            from pytest_bdd.utils import dump_obj


            @scenario("outline.feature", "Outline with escaped pipe character")
            def test_outline_with_escaped_pipe_character(request):
                pass


            @given(parsers.parse("I print the {string}"))
            def i_print_the_string(string):
                dump_obj(string)
            """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=7)
    assert collect_dumped_objects(result) == [
        r"bork",
        r"|bork",
        r"bork |",
        r"bork||bork",
        r"|",
        r"bork      \\",
        r"bork    \\|",
    ]
