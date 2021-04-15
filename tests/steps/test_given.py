"""Given tests."""
import textwrap


def test_given_injection(testdir):
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
