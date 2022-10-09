"""StepHandler arguments tests."""

from pytest import mark


@mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import cfparse",  # Deprecated
        "from parse_type.cfparse import Parser as cfparse",
    ],
)
def test_every_step_takes_param_with_the_same_name(testdir, parser_import_string):
    """Test every step takes param with the same name."""
    testdir.makefile(
        ".feature",
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

    testdir.makepyfile(
        """\
        import pytest
        from pytest_bdd import given, when, then, scenario
        """
        f"{parser_import_string}"
        """
        @scenario("arguments.feature", "Every step takes a parameter with the same name")
        def test_arguments():
            pass

        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]


        @given(cfparse("I have {euro:d} Euro"))
        def i_have(euro, values):
            assert euro == values.pop(0)


        @when(cfparse("I pay {} Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)


        @then(cfparse("I should have {euro:d} Euro"))
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import cfparse",  # Deprecated
        "from parse_type.cfparse import Parser as cfparse",
    ],
)
def test_argument_in_when(testdir, parser_import_string):
    """Test step arguments in when steps."""
    testdir.makefile(
        ".feature",
        arguments="""\
            Feature: StepHandler arguments
                Scenario: Argument in when
                    Given I have an argument 1
                    When I get argument 5
                    Then My argument should be 5
            """,
    )

    testdir.makepyfile(
        """\
        import pytest
        from pytest_bdd import given, when, then, scenario
        """
        f"{parser_import_string}"
        """
        @scenario("arguments.feature", "Argument in when")
        def test_arguments():
            pass


        @pytest.fixture
        def arguments():
            return dict()


        @given(cfparse("I have an argument {arg:Number}", extra_types=dict(Number=int)))
        def argument(arguments, arg):
            arguments["arg"] = arg


        @when(cfparse("I get argument {arg:d}"))
        def get_argument(arguments, arg):
            arguments["arg"] = arg


        @then(cfparse("My argument should be {arg:d}"))
        def assert_that_my_argument_is_arg(arguments, arg):
            assert arguments["arg"] == arg
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
