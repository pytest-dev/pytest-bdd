"""StepHandler arguments tests."""

from pytest import mark


@mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import parse",
        "from parse import Parser as parse",
    ],
)
def test_every_steps_takes_param_with_the_same_name(testdir, parser_import_string):
    testdir.makefile(
        ".feature",
        # language=gherkin
        arguments="""\
            Feature: StepHandler arguments
                Scenario: Every step takes a parameter with the same name
                    Given I have 1 Euro
                    When I pay 2 Euro
                    And I pay 1 Euro
                    Then I should have 0 Euro
                    # In my dream...
                    And I should have 999999 Euro
            """,
    )

    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from pytest_bdd import given, when, then, scenario
        """
        f"{parser_import_string}"
        """

        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]

        @given(parse("I have {euro:d} Euro"))
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(parse("I pay {} Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)

        @then(parse("I should have {euro:d} Euro"))
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import parse",
        "from parse import Parser as parse",
    ],
)
def test_argument_in_when_step_1(testdir, parser_import_string):
    testdir.makefile(
        ".feature",
        # language=gherkin
        arguments="""\
            Feature: StepHandler arguments
                Scenario: Argument in when
                    Given I have an argument 1
                    When I get argument 5
                    Then My argument should be 5
            """,
    )

    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from pytest_bdd import given, when, then
        """
        f"{parser_import_string}"
        """
        @pytest.fixture
        def arguments():
            return dict()

        @given(parse("I have an argument {arg:Number}", extra_types=dict(Number=int)))
        def argument(arguments, arg):
            arguments["arg"] = arg

        @when(parse("I get argument {arg:d}"))
        def get_argument(arguments, arg):
            arguments["arg"] = arg

        @then(parse("My argument should be {arg:d}"))
        def assert_that_my_argument_is_arg(arguments, arg):
            assert arguments["arg"] == arg

        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
