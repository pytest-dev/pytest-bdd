"""Scenario Outline with empty example values tests."""
import textwrap


STEPS = """\
from pytest_bdd import given, when, then


@given("there are <start> cucumbers")
def start_cucumbers(start):
    pass


@when("I eat <eat> cucumbers")
def eat_cucumbers(eat):
    pass


@then("I should have <left> cucumbers")
def should_have_left_cucumbers(left):
    pass

"""


def test_scenario_with_empty_example_values(testdir):
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with empty example values
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    | #     |     |      |
            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd.utils import get_parametrize_markers_args
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with empty example values")
        def test_outline(request):
            assert get_parametrize_markers_args(request.node) == ([u"start", u"eat", u"left"], [["#", "", ""]])

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_scenario_with_empty_example_values_vertical(testdir):
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with empty example values vertical
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples: Vertical
                    | start | # |
                    | eat   |   |
                    | left  |   |
            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd.utils import get_parametrize_markers_args
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with empty example values vertical")
        def test_outline(request):
            assert get_parametrize_markers_args(request.node) == ([u"start", u"eat", u"left"], [["#", "", ""]])

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
