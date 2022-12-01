"""Test no strict gherkin for sections."""


def test_background_no_strict_gherkin(testdir):
    """Test background no strict gherkin."""
    testdir.makepyfile(
        test_gherkin=f"""\
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
                return dict()

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

    testdir.makefile(
        ".feature",
        no_strict_gherkin_background="""\
            Feature: No strict Gherkin Background support

                Background:
                    When foo has a value "bar"
                    And foo is not boolean
                    And foo has not a value "baz"

                Scenario: Test background
            """,
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_scenario_no_strict_gherkin(testdir):
    """Test scenario no strict gherkin."""
    testdir.makepyfile(
        test_gherkin=f"""\
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
                return dict()

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

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
