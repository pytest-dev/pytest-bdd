"""StepHandler arguments tests."""


def test_heuristic_parser(
    testdir,
):
    testdir.makefile(
        ".feature",
        # language=gherkin
        arguments="""\
            Feature: StepHandler arguments
                Scenario: Every step takes a parameter with the same name
                    Given I have a wallet
                    Given I have 6 Euro
                    When I lose 3 Euro
                    And I pay 2 Euro
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

        @pytest.fixture
        def values():
            return [6, 3, 2, 1, 0, 999999]

        @given("I have a wallet", param_defaults={'wallet': 'wallet'})
        def i_have_wallet(wallet):
            assert wallet == 'wallet'

        @given("I have {int} Euro", anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_have(euro, values):
            assert euro == values.pop(0)


        @when("I pay {} Euro", anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)

        @when("I lose {euro:d} Euro", converters=dict(euro=int))
        def i_pay(euro, values, request):
            assert euro == values.pop(0)


        @then(r"I should have (\\d+) Euro", anonymous_group_names=('euro',), converters=dict(euro=int))
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
