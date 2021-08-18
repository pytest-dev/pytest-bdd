"""Scenario Outline tests."""
import textwrap

from tests.utils import assert_outcomes

STEPS = """\
from pytest_bdd import given, when, then


@given("there are <start> cucumbers", target_fixture="start_cucumbers")
def start_cucumbers(start):
    assert isinstance(start, int)
    return dict(start=start)


@when("I eat <eat> cucumbers")
def eat_cucumbers(start_cucumbers, eat):
    assert isinstance(eat, float)
    start_cucumbers["eat"] = eat


@then("I should have <left> cucumbers")
def should_have_left_cucumbers(start_cucumbers, start, eat, left):
    assert isinstance(left, str)
    assert start - eat == int(left)
    assert start_cucumbers["start"] == start
    assert start_cucumbers["eat"] == eat

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
        from pytest_bdd.utils import get_parametrize_markers_args
        from pytest_bdd import scenario

        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
            example_converters=dict(start=int, eat=float, left=str)
        )
        def test_outline(request):
            assert get_parametrize_markers_args(request.node) == (
                ["start", "eat", "left"],
                [
                    [12, 5.0, "7"],
                    [5, 4.0, "1"],
                ],
            )

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


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
        from pytest_bdd.utils import get_parametrize_markers_args
        from pytest_bdd import scenario


        @pytest.fixture(params=[1, 2, 3])
        def other_fixture(request):
            return request.param


        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
            example_converters=dict(start=int, eat=float, left=str)
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
                    | start | 12 | 2 |
                    | eat   | 5  | 1 |
                    | left  | 7  | 1 |

            """
        ),
    )

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd.utils import get_parametrize_markers_args
        from pytest_bdd import scenario

        @scenario(
            "outline.feature",
            "Outlined with vertical example table",
            example_converters=dict(start=int, eat=float, left=str)
        )
        def test_outline(request):
            assert get_parametrize_markers_args(request.node) == (
                ["start", "eat", "left"],
                [
                    [12, 5.0, "7"],
                    [2, 1.0, "1"],
                ],
            )

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2)


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
        from pytest_bdd.utils import get_parametrize_markers_args
        from pytest_bdd import given, when, then, scenario

        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
            example_converters=dict(start=int, eat=float, left=str)
        )
        def test_outline(request):
            assert get_parametrize_markers_args(request.node) == (
                ["start", "eat", "left"],
                [[12, 5.0, "7"], [5, 4.0, "1"]],
                ["fruits"],
                [["oranges"], ["apples"]],
            )

        @given("there are <start> <fruits>", target_fixture="start_fruits")
        def start_fruits(start, fruits):
            assert isinstance(start, int)
            return {fruits: dict(start=start)}


        @when("I eat <eat> <fruits>")
        def eat_fruits(start_fruits, eat, fruits):
            assert isinstance(eat, float)
            start_fruits[fruits]["eat"] = eat


        @then("I should have <left> <fruits>")
        def should_have_left_fruits(start_fruits, start, eat, left, fruits):
            assert isinstance(left, str)
            assert start - eat == int(left)
            assert start_fruits[fruits]["start"] == start
            assert start_fruits[fruits]["eat"] == eat

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=4)


def test_outline_with_escaped_pipes(testdir):
    """Test parametrized feature example table with escaped pipe characters in input."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            r"""\
            Feature: Outline With Special characters

                Scenario Outline: Outline with escaped pipe character
                    Given We have strings <string1> and <string2>
                    Then <string2> should be the base64 encoding of <string1>

                    Examples:
                    | string1      | string2          |
                    | bork         | Ym9yaw==         |
                    | \|bork       | fGJvcms=         |
                    | bork \|      | Ym9yayB8         |
                    | bork\|\|bork | Ym9ya3x8Ym9yaw== |
                    | \|           | fA==             |
                    | bork      \\ | Ym9yayAgICAgIFxc |
                    | bork    \\\| | Ym9yayAgICBcXHw= |
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
            import base64

            from pytest_bdd import scenario, given, when, then
            from pytest_bdd.utils import get_parametrize_markers_args


            @scenario("outline.feature", "Outline with escaped pipe character")
            def test_outline_with_escaped_pipe_character(request):
                pass


            @given("We have strings <string1> and <string2>")
            def we_have_strings_string1_and_string2(string1, string2):
                pass


            @then("<string2> should be the base64 encoding of <string1>")
            def string2_should_be_base64_encoding_of_string1(string2, string1):
                assert string1.encode() == base64.b64decode(string2.encode())

            """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=7)
