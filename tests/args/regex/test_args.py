"""Step arguments tests."""

import textwrap


def test_every_steps_takes_param_with_the_same_name(testdir):
    testdir.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: Step arguments
                Scenario: Every step takes a parameter with the same name
                    Given I have 1 Euro
                    When I pay 2 Euro
                    And I pay 1 Euro
                    Then I should have 0 Euro
                    And I should have 999999 Euro # In my dream...

            """
        ),
    )

    testdir.makepyfile(
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
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_argument_in_when(testdir):
    testdir.makefile(
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

    testdir.makepyfile(
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
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
