from __future__ import annotations

import textwrap


def test_asterisk_keyword(pytester):
    pytester.makefile(
        ".feature",
        asterisk=textwrap.dedent(
            """\
            Feature: Step continuation
                Scenario: Asterisk steps
                  Given I am out shopping
                  * I have eggs
                  * I have milk
                  * I have butter
                  When I check my list
                  Then I don't need anything
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenario

        @scenario("asterisk.feature", "Asterisk steps")
        def test_asterisk_steps():
            pass

        @given("I am out shopping")
        def _():
            pass


        @given("I have eggs")
        def _():
            pass


        @given("I have milk")
        def _():
            pass


        @given("I have butter")
        def _():
            pass


        @when("I check my list")
        def _():
            pass


        @then("I don't need anything")
        def _():
            pass

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
