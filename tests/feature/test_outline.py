"""Scenario Outline tests."""

from __future__ import annotations

import textwrap

from pytest_bdd.utils import collect_dumped_objects

STEPS = """\
from pytest_bdd import parsers, given, when, then
from pytest_bdd.utils import dump_obj


@given(parsers.parse("there are {start:d} cucumbers"), target_fixture="cucumbers")
def _(start):
    assert isinstance(start, int)
    dump_obj(start)
    return {"start": start}


@when(parsers.parse("I eat {eat:g} cucumbers"))
def _(cucumbers, eat):
    assert isinstance(eat, float)
    dump_obj(eat)
    cucumbers["eat"] = eat


@then(parsers.parse("I should have {left} cucumbers"))
def _(cucumbers, left):
    assert isinstance(left, str)
    dump_obj(left)
    assert cucumbers["start"] - cucumbers["eat"] == int(left)

"""


def test_outlined(pytester):
    pytester.makefile(
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

    pytester.makeconftest(textwrap.dedent(STEPS))

    pytester.makepyfile(
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
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=2)
    # fmt: off
    assert collect_dumped_objects(result) == [
        12, 5.0, "7",
        5, 4.0, "1",
    ]
    # fmt: on


def test_multiple_outlined(pytester):
    pytester.makefile(
        ".feature",
        outline_multi_example=textwrap.dedent(
            """\
            Feature: Outline With Multiple Examples
                Scenario Outline: Outlined given, when, thens with multiple examples tables
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    @positive
                    Examples: Positive results
                        | start | eat | left |
                        |  12   |  5  |  7   |
                        |  5    |  4  |  1   |

                    @negative
                    Examples: Negative results
                        | start | eat | left |
                        |  3    |  9  |  -6  |
                        |  1    |  4  |  -3  |
            """
        ),
    )

    pytester.makeconftest(textwrap.dedent(STEPS))

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenarios

        scenarios('outline_multi_example.feature')

        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=4)
    # fmt: off
    assert collect_dumped_objects(result) == [
        12, 5.0, "7",
        5, 4.0, "1",
        3, 9.0, "-6",
        1, 4.0, "-3",
    ]
    # fmt: on
    result = pytester.runpytest("-k", "positive", "-vv")
    result.assert_outcomes(passed=2, deselected=2)

    result = pytester.runpytest("-k", "positive or negative", "-vv")
    result.assert_outcomes(passed=4, deselected=0)


def test_unused_params(pytester):
    """Test parametrized scenario when the test function lacks parameters."""

    pytester.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with unused params
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left | unused_param |
                    |  12   |  5  |  7   | value        |

            """
        ),
    )
    pytester.makeconftest(textwrap.dedent(STEPS))

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with unused params")
        def test_outline(request):
            pass
        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_outlined_with_other_fixtures(pytester):
    """Test outlined scenario also using other parametrized fixture."""
    pytester.makefile(
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

    pytester.makeconftest(textwrap.dedent(STEPS))

    pytester.makepyfile(
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
    result = pytester.runpytest()
    result.assert_outcomes(passed=6)


def test_outline_with_escaped_pipes(pytester):
    """Test parametrized feature example table with escaped pipe characters in input."""
    pytester.makefile(
        ".feature",
        outline=textwrap.dedent(
            r"""Feature: Outline With Special characters

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

    pytester.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import scenario, given, parsers
            from pytest_bdd.utils import dump_obj


            @scenario("outline.feature", "Outline with escaped pipe character")
            def test_outline_with_escaped_pipe_character(request):
                pass


            @given(parsers.parse("I print the {string}"))
            def _(string):
                dump_obj(string)
            """
        )
    )
    result = pytester.runpytest("-s")
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


def test_forward_slash_in_params(pytester):
    """Test parametrised scenario when the parameter contains a slash, such in a URL."""

    pytester.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with slashes
                    Given I am in <Country>
                    Then I visit <Site>

                    Examples:
                        | Country  | Site                 |
                        | US       | https://my-site.com  |

            """
        ),
    )
    pytester.makeconftest(textwrap.dedent(STEPS))

    pytester.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import given, parsers, scenarios, then
            from pytest_bdd.utils import dump_obj

            scenarios('outline.feature')


            @given(parsers.parse("I am in {country}"))
            def _(country):
                pass


            @then(parsers.parse("I visit {site}"))
            def _(site):
                dump_obj(site)

        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)
    assert collect_dumped_objects(result) == ["https://my-site.com"]


def test_variable_reuse(pytester):
    """
    Test example parameter name and step arg do not redefine each other's value
    if the same name is used for both in different steps.
    """

    pytester.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Example parameters reuse
                Scenario Outline: Check for example parameter reuse
                    Given the param is initially set from the example table as <param>
                    When a step arg of the same name is set to "other"
                    Then the param is still set from the example table as <param>

                    Examples:
                        | param |
                        | value |

            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import given, when, then, parsers, scenarios
            from pytest_bdd.utils import dump_obj

            scenarios('outline.feature')


            @given(parsers.parse('the param is initially set from the example table as {param}'))
            def _(param):
                dump_obj(("param1", param))


            @when(parsers.re('a step arg of the same name is set to "(?P<param>.+)"'))
            def _(param):
                dump_obj(("param2", param))


            @then(parsers.parse('the param is still set from the example table as {param}'))
            def _(param):
                dump_obj(("param3", param))

        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)
    assert collect_dumped_objects(result) == [("param1", "value"), ("param2", "other"), ("param3", "value")]
