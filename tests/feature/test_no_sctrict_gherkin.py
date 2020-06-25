"""Test no strict gherkin for sections."""


def test_background_no_strict_gherkin(testdir):
    """Test background no strict gherkin."""
    prepare_test_dir(testdir)

    testdir.makefile(
        ".feature",
        no_strict_gherkin_background="""
    Feature: No strict Gherkin Background support

        Background:
            When foo has a value "bar"
            And foo is not boolean
            And foo has not a value "baz"

        Scenario: Test background

    """,
    )

    result = testdir.runpytest("-k", "test_background_ok")
    result.assert_outcomes(passed=1)


def test_scenario_no_strict_gherkin(testdir):
    """Test scenario no strict gherkin."""
    prepare_test_dir(testdir)

    testdir.makefile(
        ".feature",
        no_strict_gherkin_scenario="""
    Feature: No strict Gherkin Scenario support

        Scenario: Test scenario
            When foo has a value "bar"
            And foo is not boolean
            And foo has not a value "baz"

    """,
    )

    result = testdir.runpytest("-k", "test_scenario_ok")
    result.assert_outcomes(passed=1)


def prepare_test_dir(testdir):
    """Test scenario no strict gherkin."""
    testdir.makepyfile(
        test_gherkin="""
        import pytest

        from pytest_bdd import (
            when,
            scenario,
        )

        def test_scenario_ok(request):
            @scenario(
                "no_strict_gherkin_scenario.feature",
                "Test scenario",
            )
            def test():
                pass

            test(request)

        def test_background_ok(request):
            @scenario(
                "no_strict_gherkin_background.feature",
                "Test background",
            )
            def test():
                pass

            test(request)

        @pytest.fixture
        def foo():
            return {}

        @when('foo has a value "bar"')
        def bar(foo):
            foo["bar"] = "bar"
            return foo["bar"]


        @when('foo is not boolean')
        def not_boolean(foo):
            assert foo is not bool


        @when('foo has not a value "baz"')
        def has_not_baz(foo):
            assert "baz" not in foo
    """
    )
