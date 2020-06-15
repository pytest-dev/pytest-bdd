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
        def i_have(euro, values):
            assert euro == values.pop(0)


        @when(parsers.re(r"I pay (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)


        @then(parsers.re(r"I should have (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def i_should_have(euro, values):
            assert euro == values.pop(0)

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_argument_in_when_step_1(testdir):
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
        from pytest_bdd import parsers, given, when, then, scenario

        @scenario("arguments.feature", "Argument in when, step 1")
        def test_arguments():
            pass

        @given(parsers.re(r"I have an argument (?P<arg>\d+)"))
        def argument(arg):
            return dict(arg=arg)


        @when(parsers.re(r"I get argument (?P<arg>\d+)"))
        def get_argument(argument, arg):
            argument["arg"] = arg


        @then(parsers.re(r"My argument should be (?P<arg>\d+)"))
        def assert_that_my_argument_is_arg(argument, arg):
            assert argument["arg"] == arg

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_argument_in_when_step_2(testdir):
    testdir.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: Step arguments
                Scenario: Argument in when, step 2
                    Given I have an argument 1
                    When I get argument 10
                    Then My argument should be 10
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            r"""
        from pytest_bdd import parsers, given, when, then, scenario

        @scenario("arguments.feature", "Argument in when, step 2")
        def test_arguments():
            pass

        @given(parsers.re(r"I have an argument (?P<arg>\d+)"))
        def argument(arg):
            return dict(arg=arg)


        @when(parsers.re(r"I get argument (?P<arg>\d+)"))
        def get_argument(argument, arg):
            argument["arg"] = arg


        @then(parsers.re(r"My argument should be (?P<arg>\d+)"))
        def assert_that_my_argument_is_arg(argument, arg):
            assert argument["arg"] == arg

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_multiple_given(testdir):
    """Using the same given fixture raises an error."""
    testdir.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: Step arguments
                Scenario: Using the same given fixture raises an error
                    Given I have 1 Euro
                    And I have 2 Euro
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            r"""
        from pytest_bdd import parsers, given, scenario

        @scenario("arguments.feature", "Using the same given fixture raises an error")
        def test_arguments():
            pass

        @given(parsers.re(r"I have (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def i_have(euro):
            return euro

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        '*GivenAlreadyUsed: Fixture "i_have" that implements this "I have 2 Euro" given step has been already used.*'
    )
