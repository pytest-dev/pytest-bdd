"""Function name same as step name."""

from __future__ import annotations

import textwrap


def test_when_function_name_same_as_step_name(pytester):
    pytester.makefile(
        ".feature",
        same_name=textwrap.dedent(
            """\
            Feature: Function name same as step name
                Scenario: When function name same as step name
                    When something
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import when, scenario

        @scenario("same_name.feature", "When function name same as step name")
        def test_same_name():
            pass

        @when("something")
        def _():
            return "something"
        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
