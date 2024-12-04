"""Test automatic feature file collection."""


def test_auto_collect_disabled_by_default(pytester):
    """Auto collection should be disabled by default."""
    pytester.makefile(
        ".feature",
        feature="""
        Feature: Auto collect
            Scenario: Test auto collect
                Given I have a feature
                When I run pytest
                Then it should not be collected
    """,
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=0, failed=0, skipped=0)


def test_auto_collect_enabled(pytester):
    """Auto collection should work when enabled."""
    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        bdd_auto_collect_features = true
    """,
    )

    pytester.makefile(
        ".feature",
        feature="""
        Feature: Auto collect
            Scenario: Test auto collect
                Given I have a feature
                When I run pytest
                Then it should be collected
    """,
    )

    pytester.makeconftest(
        """
        from pytest_bdd import given, when, then

        @given("I have a feature")
        def have_feature():
            pass

        @when("I run pytest")
        def run_pytest():
            pass

        @then("it should be collected")
        def should_be_collected():
            pass
    """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_auto_collect_respects_bound_scenarios(pytester):
    """Auto collection should not collect scenarios that are already bound."""
    pytester.makefile(
        ".ini",
        pytest="""
        [pytest]
        bdd_auto_collect_features = true
    """,
    )

    pytester.makefile(
        ".feature",
        feature="""
        Feature: Auto collect
            Scenario: Bound scenario
                Given I have a feature
                When I run pytest
                Then it should be collected once

            Scenario: Unbound scenario
                Given I have a feature
                When I run pytest
                Then it should be collected once
    """,
    )

    pytester.makeconftest(
        """
        from pytest_bdd import given, when, then, scenario

        @scenario('feature.feature', 'Bound scenario')
        def test_bound():
            pass

        @given("I have a feature")
        def have_feature():
            pass

        @when("I run pytest")
        def run_pytest():
            pass

        @then("it should be collected once")
        def should_be_collected():
            pass
    """
    )

    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=2)  # Both scenarios should pass
    # Ensure bound scenario is only collected once
    result.stdout.fnmatch_lines(["*test_bound PASSED*"])
