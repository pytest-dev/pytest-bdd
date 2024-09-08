"""Test no strict gherkin for sections."""


def test_background_no_strict_gherkin(pytester):
    """Test background no strict gherkin."""
    pytester.makepyfile(
        test_gherkin="""
        import pytest

        from pytest_bdd import when, scenario

        @scenario(
            "no_strict_gherkin_background.feature",
            "Test background",
        )
        def test_background():
            pass


        @pytest.fixture
        def foo():
            return {}

        @when('foo has a value "bar"')
        def _(foo):
            foo["bar"] = "bar"
            return foo["bar"]


        @when('foo is not boolean')
        def _(foo):
            assert foo is not bool


        @when('foo has not a value "baz"')
        def _(foo):
            assert "baz" not in foo
    """
    )

    pytester.makefile(
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

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_scenario_no_strict_gherkin(pytester):
    """Test scenario no strict gherkin."""
    pytester.makepyfile(
        test_gherkin="""
        import pytest

        from pytest_bdd import when, scenario

        @scenario(
            "no_strict_gherkin_scenario.feature",
            "Test scenario",
        )
        def test_scenario():
            pass


        @pytest.fixture
        def foo():
            return {}

        @when('foo has a value "bar"')
        def _(foo):
            foo["bar"] = "bar"
            return foo["bar"]


        @when('foo is not boolean')
        def _(foo):
            assert foo is not bool


        @when('foo has not a value "baz"')
        def _(foo):
            assert "baz" not in foo
    """
    )

    pytester.makefile(
        ".feature",
        no_strict_gherkin_scenario="""
    Feature: No strict Gherkin Scenario support

        Scenario: Test scenario
            When foo has a value "bar"
            And foo is not boolean
            And foo has not a value "baz"

    """,
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
