"""Test step alias when decorated multiple times."""

import textwrap


def test_step_alias(testdir):
    testdir.makefile(
        ".feature",
        alias=textwrap.dedent(
            """\
            Feature: Step aliases
                Scenario: Multiple step aliases
                    Given I have an empty list
                    And I have foo (which is 1) in my list
                    # Alias of the "I have foo (which is 1) in my list"
                    And I have bar (alias of foo) in my list

                    When I do crash (which is 2)
                    And I do boom (alias of crash)
                    Then my list should be [1, 1, 2, 2]
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenario

        @scenario("alias.feature", "Multiple step aliases")
        def test_alias():
            pass


        @given("I have an empty list", target_fixture="results")
        def results():
            return []


        @given("I have foo (which is 1) in my list")
        @given("I have bar (alias of foo) in my list")
        def foo(results):
            results.append(1)


        @when("I do crash (which is 2)")
        @when("I do boom (alias of crash)")
        def crash(results):
            results.append(2)


        @then("my list should be [1, 1, 2, 2]")
        def check_results(results):
            assert results == [1, 1, 2, 2]
        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
