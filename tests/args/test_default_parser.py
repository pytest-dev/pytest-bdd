import textwrap


def test_tags_selector(pytester):
    """Test tests selection by tags."""
    pytester.makefile(
        ".ini",
        pytest=textwrap.dedent(
            """
    [pytest]
    bdd_default_parser = string
    """
        ),
    )
    pytester.makefile(
        ".feature",
        parser=textwrap.dedent(
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
        from pytest_bdd import parsers, given, when, then, scenarios

        scenarios("parser.feature")


        @pytest.fixture
        def values():
            return [1, 2, 1, 0, 999999]


        @given("I have {euro:d} Euro")
        def _(euro, values):
            assert euro == values.pop(0)


        @when("I pay {euro:d} Euro")
        def _(euro, values, request):
            assert euro == values.pop(0)


        @then("I should have {euro:d} Euro")
        def _(euro, values):
            assert euro == values.pop(0)

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
