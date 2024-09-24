"""Given tests."""

import textwrap


def test_given_injection_single_value(pytester):
    pytester.makefile(
        ".feature",
        given=textwrap.dedent(
            """\
            Feature: Given
                Scenario: Test given fixture injection
                    Given I have injected single value
                    Then foo should be "injected foo"
                    Given I have injected tuple value
                    Then foo should be tuple value
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, then, scenario

        @scenario("given.feature", "Test given fixture injection")
        def test_given():
            pass

        @given("I have injected single value", target_fixture="foo")
        def _():
            return "injected foo"

        @given("I have injected tuple value", target_fixture="foo")
        def _():
            return ("injected foo", {"city": ["Boston", "Houston"]}, [10,20,30],)

        @then('foo should be "injected foo"')
        def _(foo):
            assert foo == "injected foo"

        @then('foo should be tuple value')
        def _(foo):
            assert foo == ("injected foo", {"city": ["Boston", "Houston"]}, [10,20,30],)
        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_given_injection_multiple_values(pytester):
    pytester.makefile(
        ".feature",
        given=textwrap.dedent(
            """\
            Feature: Given
                Scenario: Test given fixture injection
                    Given I have injecting given values
                    Then values should be received
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, then, scenario

        @scenario("given.feature", "Test given fixture injection")
        def test_given():
            pass

        @given("I have injecting given values", target_fixture="foo,city,numbers")
        def _():
            return ("injected foo", {"city": ["Boston", "Houston"]}, [10,20,30],)


        @then("values should be received")
        def _(foo, city, numbers):
            assert foo == "injected foo"
            assert city == {"city": ["Boston", "Houston"]}
            assert numbers == [10,20,30]

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
