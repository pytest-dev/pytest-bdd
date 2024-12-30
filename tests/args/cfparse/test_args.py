"""Step arguments tests."""

from __future__ import annotations

import textwrap


def test_every_step_takes_param_with_the_same_name(pytester):
    """Test every step takes param with the same name."""
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
            """\
        import pytest
        from pytest_bdd import parsers, given, when, then, scenario

        @scenario("arguments.feature", "Every step takes a parameter with the same name")
        def test_arguments():
            pass

        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]


        @given(parsers.cfparse("I have {euro:d} Euro"))
        def _(euro, values):
            assert euro == values.pop(0)


        @when(parsers.cfparse("I pay {euro:d} Euro"))
        def _(euro, values, request):
            assert euro == values.pop(0)


        @then(parsers.cfparse("I should have {euro:d} Euro"))
        def _(euro, values):
            assert euro == values.pop(0)

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_argument_in_when(pytester):
    """Test step arguments in when steps."""
    pytester.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: Step arguments
                Scenario: Argument in when
                    Given I have an argument 1
                    When I get argument 5
                    Then My argument should be 5
            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import parsers, given, when, then, scenario

        @scenario("arguments.feature", "Argument in when")
        def test_arguments():
            pass


        @pytest.fixture
        def arguments():
            return dict()


        @given(parsers.cfparse("I have an argument {arg:Number}", extra_types=dict(Number=int)))
        def _(arguments, arg):
            arguments["arg"] = arg


        @when(parsers.cfparse("I get argument {arg:d}"))
        def _(arguments, arg):
            arguments["arg"] = arg


        @then(parsers.cfparse("My argument should be {arg:d}"))
        def _(arguments, arg):
            assert arguments["arg"] == arg

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
