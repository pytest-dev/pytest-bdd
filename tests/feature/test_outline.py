"""Scenario Outline tests."""
import textwrap

from pytest_bdd.utils import collect_dumped_objects
from tests.utils import assert_outcomes

STEPS = """\
from pytest_bdd import parsers, given, when, then
from pytest_bdd.utils import dump_obj


@given(parsers.parse("there are {start} cucumbers"), target_fixture="start_cucumbers")
def start_cucumbers(start):
    assert isinstance(start, str)
    start = int(start)
    dump_obj(start)
    return dict(start=start)


@when(parsers.parse("I eat {eat} cucumbers"))
def eat_cucumbers(start_cucumbers, eat):
    assert isinstance(eat, str)
    eat = int(eat)
    dump_obj(eat)
    start_cucumbers["eat"] = eat


@then(parsers.parse("I should have {left} cucumbers"))
def should_have_left_cucumbers(start_cucumbers, left):
    assert isinstance(left, str)
    left = int(left)
    dump_obj(left)
    assert left == start_cucumbers["start"] - start_cucumbers["eat"]

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
                    |  5    |  4  |  43  | # Control case. This should fail.

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
    result = testdir.runpytest()
    result.assert_outcomes(passed=2, failed=1)


def test_wrongly_outlined(testdir):
    """Test parametrized scenario when the test function lacks parameters."""

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with wrong examples
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left | unknown_param |
                    |  12   |  5  |  7   | value         |

            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with wrong examples")
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        '*ScenarioExamplesNotValidError: Scenario "Outlined with wrong examples"*has not valid examples*',
    )
    result.stdout.fnmatch_lines("*should match set of example values [[]'eat', 'left', 'start', 'unknown_param'[]].*")


def test_wrong_vertical_examples_scenario(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples: Vertical
                    | start | 12 | 2 |
                    | start | 10 | 1 |
                    | left  | 7  | 1 |
            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with wrong vertical example table")
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        "*Scenario has not valid examples. Example rows should contain unique parameters. "
        '"start" appeared more than once.*'
    )


def test_wrong_vertical_examples_feature(testdir):
    """Test parametrized feature vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outlines

                Examples: Vertical
                | start | 12 | 2 |
                | start | 10 | 1 |
                | left  | 7  | 1 |

                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers
            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with wrong vertical example table")
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        "*Feature has not valid examples. Example rows should contain unique parameters. "
        '"start" appeared more than once.*'
    )


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


def test_vertical_example(testdir):
    """Test outlined scenario with vertical examples table."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples: Vertical
                    | start | 12 | 2 | 2  |
                    | eat   | 5  | 1 | 1  |
                    | left  | 7  | 1 | 42 |

                    # The last column is the control case, to verify that the scenario fails

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
            "Outlined with vertical example table",
        )
        def test_outline():
            pass
        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2, failed=1)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, 5, 7,
        2, 1, 1,
        2, 1, 42,
    ]
    # fmt: on


def test_outlined_feature(testdir):
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline

                Examples:
                | start | eat | left |
                |  12   |  5  |  7   |
                |  5    |  4  |  1   |

                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | fruits  |
                    | oranges |
                    | apples  |
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, scenario, parsers
        from pytest_bdd.utils import dump_obj

        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
        )
        def test_outline():
            pass

        @given(parsers.parse("there are {start} {fruits}"), target_fixture="start_fruits")
        def start_fruits(start, fruits):
            start = int(start)
            dump_obj(start, fruits)
            return {fruits: {"start": start}}


        @when(parsers.parse("I eat {eat} {fruits}"))
        def eat_fruits(start_fruits, eat, fruits):
            eat = float(eat)
            dump_obj(eat, fruits)
            start_fruits[fruits]["eat"] = eat


        @then(parsers.parse("I should have {left} {fruits}"))
        def should_have_left_fruits(start_fruits, start, eat, left, fruits):
            left = int(left)
            dump_obj(left, fruits)
            assert left == start_fruits[fruits]["start"] - start_fruits[fruits]["eat"]

        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=4)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, "oranges", 5, "oranges", 7, "oranges",
        12, "apples", 5, "apples", 7, "apples",
        5, "oranges", 4, "oranges", 1, "oranges",
        5, "apples", 4, "apples", 1, "apples",
    ]
    # fmt: on


def test_outline_with_escaped_pipes(testdir):
    """Test parametrized feature example table with escaped pipe characters in input."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            r"""\
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
