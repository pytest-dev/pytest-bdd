"""Step arguments tests."""

from __future__ import annotations

import textwrap


def test_every_steps_takes_param_with_the_same_name(pytester):
    pytester.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: Step arguments
                Scenario: Every step takes a parameter with the same name
                    Given I have 1 Euro
                    When I pay 2 Euro
                    And I pay 1 Euro
                    Then I should have 0 Euro
                    And I should have 999999 Euro

            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            r"""
        import pytest
        from pytest_bdd import parsers, given, when, then, scenario

        @scenario("arguments.feature", "Every step takes a parameter with the same name")
        def test_arguments():
            pass

        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]

        @given(parsers.re(r"I have (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def _(euro, values):
            assert euro == values.pop(0)


        @when(parsers.re(r"I pay (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def _(euro, values, request):
            assert euro == values.pop(0)


        @then(parsers.re(r"I should have (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def _(euro, values):
            assert euro == values.pop(0)

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_exact_match(pytester):
    """Test that parsers.re does an exact match (fullmatch) of the whole string.

    This tests exists because in the past we only used re.match, which only finds a match at the beginning
    of the string, so if there were any more characters not matching at the end, they were ignored"""

    pytester.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: Step arguments
                Scenario: Every step takes a parameter with the same name
                    Given I have 2 Euro
                    # Step that should not be found:
                    When I pay 1 Euro by mistake
                    Then I should have 1 Euro left
            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            r"""
        import pytest
        from pytest_bdd import parsers, given, when, then, scenarios

        scenarios("arguments.feature")

        @given(parsers.re(r"I have (?P<amount>\d+) Euro"), converters={"amount": int}, target_fixture="wallet")
        def _(amount):
            return {"EUR": amount}


        # Purposefully using a re that will not match the step "When I pay 1 Euro and 50 cents"
        @when(parsers.re(r"I pay (?P<amount>\d+) Euro"), converters={"amount": int})
        def _(amount, wallet):
            wallet["EUR"] -= amount


        @then(parsers.re(r"I should have (?P<amount>\d+) Euro left"), converters={"amount": int})
        def _(amount, wallet):
            assert wallet["EUR"] == amount

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        '*StepDefinitionNotFoundError: Step definition is not found: When "I pay 1 Euro by mistake"*'
    )


def test_argument_in_when(pytester):
    pytester.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: Step arguments
                Scenario: Argument in when, step 1
                    Given I have an argument 1
                    When I get argument 5
                    Then My argument should be 5
            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            r"""
        import pytest
        from pytest_bdd import parsers, given, when, then, scenario


        @pytest.fixture
        def arguments():
            return dict()


        @scenario("arguments.feature", "Argument in when, step 1")
        def test_arguments():
            pass

        @given(parsers.re(r"I have an argument (?P<arg>\d+)"))
        def _(arguments, arg):
            arguments["arg"] = arg


        @when(parsers.re(r"I get argument (?P<arg>\d+)"))
        def _(arguments, arg):
            arguments["arg"] = arg


        @then(parsers.re(r"My argument should be (?P<arg>\d+)"))
        def _(arguments, arg):
            assert arguments["arg"] == arg

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
