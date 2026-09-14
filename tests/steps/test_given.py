"""Given tests."""

from __future__ import annotations

import textwrap


def test_given_injection(pytester):
    pytester.makefile(
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
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, then, scenario

        @scenario("given.feature", "Test given fixture injection")
        def test_given():
            pass

        @given("I have injecting given", target_fixture="foo")
        def _():
            return "injected foo"


        @then('foo should be "injected foo"')
        def _(foo):
            assert foo == "injected foo"

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_given_injection_no_deprecation_warning(pytester):
    """Injecting a target fixture must not emit pytest deprecation warnings."""
    pytester.makefile(
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
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, then, scenario

        @scenario("given.feature", "Test given fixture injection")
        def test_given():
            pass


        @given("I have injecting given", target_fixture="foo")
        def _():
            return "injected foo"


        @then('foo should be "injected foo"')
        def _(foo):
            assert foo == "injected foo"

        """
        )
    )
    # fmt: off
    result = pytester.runpytest(
        "-W", "error::DeprecationWarning",
        "-W", "error::PendingDeprecationWarning",
        "-W", "ignore:A private pytest class or function was used:pytest.PytestDeprecationWarning",
    )
    # fmat: on
    result.assert_outcomes(passed=1)
