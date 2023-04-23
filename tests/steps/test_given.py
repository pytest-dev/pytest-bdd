"""Given tests."""
import textwrap


def test_given_injection_single_value(testdir):
    testdir.makefile(
        ".feature",
        given=textwrap.dedent(
            """\
            Feature: Given
                Scenario: Test given fixture injection
                    Given I have injecting given
                    Then foo should be "injected foo"
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, then, scenario

        @scenario("given.feature", "Test given fixture injection")
        def test_given():
            pass

        @given("I have injecting given", target_fixture="foo")
        def injecting_given():
            return "injected foo"


        @then('foo should be "injected foo"')
        def foo_is_injected_foo(foo):
            assert foo == "injected foo"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)

def test_given_injection_multiple_values(testdir):
    testdir.makefile(
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
    testdir.makepyfile(
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
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
