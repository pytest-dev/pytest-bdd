"""StepHandler arguments tests."""
from typing import TYPE_CHECKING

from pytest import mark

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.compatibility.pytest import Testdir


@mark.parametrize(
    "parser_import_string",
    [
        # language=python
        """
        from pytest_bdd.parsers import cucumber_expression
        assert cucumber_expression
        """,
        # language=python
        """
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
        from functools import partial
        from cucumber_expressions.expression import CucumberExpression
        cucumber_expression = partial(CucumberExpression, parameter_type_registry = ParameterTypeRegistry())
        """,
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
        """
        f"{parser_import_string}"
        """

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


def test_cucumber_expression_complex_type(testdir: "Testdir", tmp_path):
    """Test comments inside scenario."""
    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from cucumber_expressions.parameter_type import ParameterType
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

        from pytest_bdd import given
        from pytest_bdd.parsers import cucumber_expression


        class Coordinate:
            def __init__(self, x: int, y: int, z: int):
                self.x = x
                self.y = y
                self.z = z

            def __eq__(self, other):
                return all([
                    isinstance(other, Coordinate),
                    self.x == other.x,
                    self.y == other.y,
                    self.z == other.z,
                ])


        @pytest.fixture
        def parameter_type_registry():
            _parameter_type_registry = ParameterTypeRegistry()
            _parameter_type_registry.define_parameter_type(
                ParameterType(
                    "coordinate",
                    r"(\\d+),\\s*(\\d+),\\s*(\\d+)",
                    Coordinate,
                    lambda x, y, z: Coordinate(int(x), int(y), int(z)),
                    True,
                    False,
                )
            )

            return _parameter_type_registry


        @given(
            cucumber_expression(
                "A {int} thick line from {coordinate} to {coordinate}"
            ),
            anonymous_group_names=['thick', 'start', 'end'],
        )
        def cukes_count(thick, start, end):
            assert Coordinate(10, 20, 30) == start
            assert Coordinate(40, 50, 60) == end
            assert thick == 5

        """
    )
    testdir.makefile(
        ".feature",
        # language=gherkin
        balls="""
        Feature: minimal

          Scenario: Thick line
            Given A 5 thick line from 10,20,30 to 40,50,60

        """,
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@mark.parametrize(
    "parser_import_string",
    [
        # language=python
        "from pytest_bdd.parsers import cucumber_regular_expression as CucumberRegularExpression",
        # language=python
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
