"""StepHandler arguments tests."""

from pytest import mark


@mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import cucumber_expression as CucumberExpression",
        "from cucumber_expressions.expression import CucumberExpression",
    ],
)
def test_cucumber_expression(
    testdir,
    parser_import_string,
):
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
        from pytest_bdd import given, when, then
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
        from functools import partial
        """
        f"{parser_import_string}"
        """

        cucumber_expression = partial(CucumberExpression, parameter_type_registry = ParameterTypeRegistry())

        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]

        """
        """
        @given(cucumber_expression("I have {int} Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(cucumber_expression("I pay {} Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)

        @then(cucumber_expression("I should have {int} Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@mark.parametrize(
    "parser_import_string",
    [
        "from pytest_bdd.parsers import cucumber_regular_expression as CucumberRegularExpression",
        "from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression",
    ],
)
def test_cucumber_regular_expression(
    testdir,
    parser_import_string,
):
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
        from pytest_bdd import given, when, then
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
        from functools import partial
        """
        f"{parser_import_string}"
        """

        cucumber_expression = partial(CucumberRegularExpression, parameter_type_registry = ParameterTypeRegistry())

        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]

        @given(cucumber_expression(r"I have (\\d+) Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(cucumber_expression("I pay (.*) Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)

        @then(cucumber_expression(r"I should have (\\d+) Euro"), anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
