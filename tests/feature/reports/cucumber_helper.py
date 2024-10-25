import textwrap


class OfType:
    """Helper object to help compare object type to initialization type"""

    def __init__(self, type: type | None = None) -> None:
        self.type = type

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.type) if self.type else True


def create_test(pytester):
    pytester.makefile(
        ".ini",
        pytest=textwrap.dedent(
            """
    [pytest]
    markers =
        scenario-passing-tag
        scenario-failing-tag
        scenario-outline-passing-tag
        feature-tag
    """
        ),
    )
    pytester.makefile(
        ".feature",
        test=textwrap.dedent(
            """
    @feature-tag
    Feature: One passing scenario, one failing scenario

        @scenario-passing-tag
        Scenario: Passing
            Given a passing step
            And some other passing step

        @scenario-failing-tag
        Scenario: Failing
            Given a passing step
            And a failing step

        @scenario-outline-passing-tag
        Scenario Outline: Passing outline
            Given type <type> and value <value>

            Examples: example1
            | type    | value  |
            | str     | hello  |
            | int     | 42     |
            | float   | 1.0    |
    """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
        import pytest
        from pytest_bdd import given, when, scenario, parsers

        @given('a passing step')
        def _():
            return 'pass'

        @given('some other passing step')
        def _():
            return 'pass'

        @given('a failing step')
        def _():
            raise Exception('Error')

        @given(parsers.parse('type {type} and value {value}'))
        def _():
            return 'pass'

        @scenario('test.feature', 'Passing')
        def test_passing():
            pass

        @scenario('test.feature', 'Failing')
        def test_failing():
            pass

        @scenario('test.feature', 'Passing outline')
        def test_passing_outline():
            pass
    """
        )
    )
