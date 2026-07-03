"""Scenario Outline with empty example values tests."""

from __future__ import annotations

import textwrap

from pytest_bdd.utils import collect_dumped_objects

STEPS = """\
from pytest_bdd import given, when, then, parsers
from pytest_bdd.utils import dump_obj

# Using `parsers.re` so that we can match empty values

@given(parsers.re("there are (?P<start>.*?) cucumbers"))
def _(start):
    dump_obj(start)


@when(parsers.re("I eat (?P<eat>.*?) cucumbers"))
def _(eat):
    dump_obj(eat)


@then(parsers.re("I should have (?P<left>.*?) cucumbers"))
def _(left):
    dump_obj(left)

"""


def test_scenario_with_empty_example_values(pytester):
    pytester.makefile(
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
    pytester.makeconftest(textwrap.dedent(STEPS))

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd.utils import dump_obj
        from pytest_bdd import scenario
        import json

        @scenario("outline.feature", "Outlined with empty example values")
        def test_outline():
            pass
        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)
    assert collect_dumped_objects(result) == ["#", "", ""]
