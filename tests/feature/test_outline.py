"""Scenario Outline tests."""
from __future__ import unicode_literals
import re
import textwrap

import pytest

from pytest_bdd import given, when, then, scenario
from pytest_bdd import exceptions
from pytest_bdd.utils import get_parametrize_markers_args


@scenario("outline.feature", "Outlined given, when, thens", example_converters=dict(start=int, eat=float, left=str))
def test_outlined(request):
    assert get_parametrize_markers_args(request.node) == (["start", "eat", "left"], [[12, 5.0, "7"], [5, 4.0, "1"]])


@given("there are <start> cucumbers")
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


def test_wrongly_outlined(request):
    """Test parametrized scenario when the test function lacks parameters."""
    with pytest.raises(exceptions.ScenarioExamplesNotValidError) as exc:

        @scenario("outline.feature", "Outlined with wrong examples")
        def wrongly_outlined():
            pass

    assert re.match(
        r"""Scenario \"Outlined with wrong examples\" in the feature \"(.+)\" has not valid examples\. """
        r"""Set of step parameters (.+) should match set of example values """
        r"""(.+)\.""",
        exc.value.args[0],
    )


def test_wrong_vertical_examples_scenario(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    features = testdir.mkdir("features")
    feature = features.join("test.feature")
    feature.write_text(
        textwrap.dedent(
            """
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
        "utf-8",
        ensure=True,
    )
    with pytest.raises(exceptions.FeatureError) as exc:

        @scenario(feature.strpath, "Outlined with wrong vertical example table")
        def wrongly_outlined():
            pass

    assert exc.value.args[0] == (
        "Scenario has not valid examples. Example rows should contain unique parameters."
        ' "start" appeared more than once'
    )


def test_wrong_vertical_examples_feature(testdir):
    """Test parametrized feature vertical example table has wrong format."""
    features = testdir.mkdir("features")
    feature = features.join("test.feature")
    feature.write_text(
        textwrap.dedent(
            """
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
        "utf-8",
        ensure=True,
    )
    with pytest.raises(exceptions.FeatureError) as exc:

        @scenario(feature.strpath, "Outlined with wrong vertical example table")
        def wrongly_outlined():
            pass

    assert exc.value.args[0] == (
        "Feature has not valid examples. Example rows should contain unique parameters."
        ' "start" appeared more than once'
    )


@pytest.fixture(params=[1, 2, 3])
def other_fixture(request):
    return request.param


@scenario("outline.feature", "Outlined given, when, thens", example_converters=dict(start=int, eat=float, left=str))
def test_outlined_with_other_fixtures(other_fixture):
    """Test outlined scenario also using other parametrized fixture."""


@scenario(
    "outline.feature", "Outlined with vertical example table", example_converters=dict(start=int, eat=float, left=str)
)
def test_vertical_example(request):
    """Test outlined scenario with vertical examples table."""
    assert get_parametrize_markers_args(request.node) == (["start", "eat", "left"], [[12, 5.0, "7"], [2, 1.0, "1"]])


@given("there are <start> <fruits>")
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


@scenario(
    "outline_feature.feature", "Outlined given, when, thens", example_converters=dict(start=int, eat=float, left=str)
)
def test_outlined_feature(request):
    assert get_parametrize_markers_args(request.node) == (
        ["start", "eat", "left"],
        [[12, 5.0, "7"], [5, 4.0, "1"]],
        ["fruits"],
        [["oranges"], ["apples"]],
    )


def test_outline_with_escaped_pipes(testdir):
    """Test parametrized feature example table with escaped pipe characters in input."""
    features = testdir.mkdir("features")
    feature = features.join("test.feature")
    feature.write_text(
        textwrap.dedent(
            r"""
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
        "utf-8",
        ensure=True,
    )

    testdir.makepyfile(
        textwrap.dedent(
            """
    import base64

    from pytest_bdd import scenario, given, when, then
    from pytest_bdd.utils import get_parametrize_markers_args


    @scenario("features/test.feature", "Outline with escaped pipe character")
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
    result.stdout.fnmatch_lines(["* 7 passed *"])
