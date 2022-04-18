"""StepHandler arguments tests."""

import textwrap

from pytest import mark


@mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import re as parse_re",
        "from re import compile as parse_re",
    ],
)
def test_every_steps_takes_param_with_the_same_name(testdir, parser_import_string):
    testdir.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: StepHandler arguments
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
            """\
        import pytest
        from pytest_bdd import given, when, then, scenario
        """
            f"{parser_import_string}"
            r"""

        @scenario("arguments.feature", "Every step takes a parameter with the same name")
        def test_arguments():
            pass

        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]

        @given(parse_re(r"I have (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def i_have(euro, values):
            assert euro == values.pop(0)


        @when(parse_re(r"I pay (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)


        @then(parse_re(r"I should have (?P<euro>\d+) Euro"), converters=dict(euro=int))
        def i_should_have(euro, values):
            assert euro == values.pop(0)

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import re as parse_re",
        "from re import compile as parse_re",
    ],
)
def test_argument_in_when(testdir, parser_import_string):
    testdir.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: StepHandler arguments
                Scenario: Argument in when, step 1
                    Given I have an argument 1
                    When I get argument 5
                    Then My argument should be 5
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenario
        """
            f"{parser_import_string}"
            r"""

        @pytest.fixture
        def arguments():
            return dict()


        @scenario("arguments.feature", "Argument in when, step 1")
        def test_arguments():
            pass

        @given(parse_re(r"I have an argument (?P<arg>\d+)"))
        def argument(arguments, arg):
            arguments["arg"] = arg


        @when(parse_re(r"I get argument (?P<arg>\d+)"))
        def get_argument(arguments, arg):
            arguments["arg"] = arg


        @then(parse_re(r"My argument should be (?P<arg>\d+)"))
        def assert_that_my_argument_is_arg(arguments, arg):
            assert arguments["arg"] == arg

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
