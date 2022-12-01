"""Scenario Outline tests."""
from operator import lt
from textwrap import dedent

from pytest import mark, param

from pytest_bdd.packaging import compare_distribution_version
from pytest_bdd.utils import collect_dumped_objects
from tests.utils import assert_outcomes

STEPS = """\
    from pytest_bdd import parsers, given, when, then
    from pytest_bdd.utils import dump_obj


    @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
    def start_cucumbers(start):
        assert isinstance(start, int)
        dump_obj(start)
        return {"start": start}


    @when(parsers.parse("I eat {eat:g} cucumbers"))
    def eat_cucumbers(start_cucumbers, eat):
        assert isinstance(eat, float)
        dump_obj(eat)
        start_cucumbers["eat"] = eat


    @then(parsers.parse("I should have {left} cucumbers"))
    def should_have_left_cucumbers(start_cucumbers, start, eat, left):
        assert isinstance(left, str)
        dump_obj(left)
        assert start - eat == int(left)
        assert start_cucumbers["start"] == start
        assert start_cucumbers["eat"] == eat
"""

STEPS_OUTLINED = """\
    from pytest_bdd import given, when, then, scenario, parsers
    from pytest_bdd.utils import dump_obj

    @scenario(
        "outline.feature",
        "Outlined given, when, thens",
        parser=Parser()
    )
    def test_outline():
        pass

    @given(parsers.parse("there are {start:d} {fruits}"), target_fixture="start_fruits")
    def start_fruits(start, fruits):
        dump_obj(start, fruits)

        assert isinstance(start, int)
        return {fruits: dict(start=start)}


    @when(parsers.parse("I eat {eat:g} {fruits}"))
    def eat_fruits(start_fruits, eat, fruits):
        dump_obj(eat, fruits)

        assert isinstance(eat, float)
        start_fruits[fruits]["eat"] = eat


    @then(parsers.parse("I should have {left} {fruits}"))
    def should_have_left_fruits(start_fruits, start, eat, left, fruits):
        dump_obj(left, fruits)

        assert isinstance(left, str)
        assert start - eat == int(left)
        assert start_fruits[fruits]["start"] == start
        assert start_fruits[fruits]["eat"] == eat
"""


@mark.parametrize(
    "examples_header",
    (
        param("Examples:", id="non_named"),
        param("Examples: Named", id="named"),
    ),
)
def test_outlined(testdir, examples_header):
    testdir.makefile(
        ".feature",
        outline=f"""\
            Feature: Outline
                Scenario Outline: Outlined given, when, thens
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    {examples_header}
                    | start | eat | left |
                    |  12   |  5  |  7   | # a comment
                    |  5    |  4  |  1   |

            """,
    )

    testdir.makeconftest(STEPS)

    testdir.makepyfile(
        f"""\
        from pytest_bdd import scenario

        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
        )
        def test_outline(request):
            pass
        """
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)
    # fmt: off
    assert collect_dumped_objects(result) == [
        12, 5.0, "7",
        5, 4.0, "1",
    ]
    # fmt: on


@mark.xfail(reason="https://github.com/cucumber/common/issues/1953")
def test_wrongly_outlined_duplicated_parameter_scenario(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Scenario Outline: Outlined with duplicated parameter example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | start | left |
                    |   12  |   10  |   7  |
                    |    2  |    1  |   1  |
            """,
    )
    testdir.makeconftest(STEPS)

    testdir.makepyfile(
        f"""\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with wrong vertical example table")
        def test_outline(request):
            pass
        """
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        "*Scenario has not valid examples. Example rows should contain unique parameters. "
        '"start" appeared more than once.*'
    )


def test_wrongly_outlined_missing_parameter_scenario(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    |   12  | 10  |   7  |
                    |    2  |  1  |
            """,
    )
    testdir.makeconftest(STEPS)

    testdir.makepyfile(
        f"""\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with wrong vertical example table")
        def test_outline(request):
            pass
        """
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines("*FeatureError*")


def test_outlined_with_other_fixtures(testdir):
    """Test outlined scenario also using other parametrized fixture."""
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Scenario Outline: Outlined given, when, thens
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   |
                    |  5    |  4  |  1   |
            """,
    )

    testdir.makeconftest(STEPS)

    testdir.makepyfile(
        f"""\
        from pytest import fixture
        from pytest_bdd import scenario

        @fixture(params=[1, 2, 3])
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
    result = testdir.runpytest()
    result.assert_outcomes(passed=6)


@mark.parametrize(
    "parser,",
    [
        param(
            "GherkinParser",
            marks=[mark.xfail(reason="https://github.com/cucumber/common/issues/1954")]
            if compare_distribution_version("gherkin-official", "24.1", lt)
            else [],
        ),
    ],
)
def test_outline_with_escaped_pipes(testdir, parser):
    """Test parametrized feature example table with escaped pipe characters in input."""
    testdir.makefile(
        ".feature",
        outline=dedent(
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
        f"""\
        from pytest_bdd import scenario, given, parsers
        from pytest_bdd.utils import dump_obj

        @scenario("outline.feature", "Outline with escaped pipe character")
        def test_outline_with_escaped_pipe_character(request):
            pass


        @given(parsers.parse("I print the {{string}}"))
        def i_print_the_string(string):
            dump_obj(string)
        """
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=7)
    assert collect_dumped_objects(result) == [
        r"bork",
        r"|bork",
        r"bork |",
        r"bork||bork",
        r"|",
        "bork      \\",
        "bork    \\|",
    ]
