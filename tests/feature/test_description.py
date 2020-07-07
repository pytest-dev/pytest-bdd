"""Test descriptions."""

import textwrap


def test_description(testdir):
    """Test description for the feature."""
    testdir.makefile(
        ".feature",
        description=textwrap.dedent(
            """\
        Feature: Description

            In order to achieve something
            I want something
            Because it will be cool
            Given it is valid description
            When it starts working
            Then I will be happy


            Some description goes here.

            Scenario: Description
                Given I have a bar
        """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import textwrap
        from pytest_bdd import given, scenario

        @scenario("description.feature", "Description")
        def test_description():
            pass


        @given("I have a bar")
        def bar():
            return "bar"

        def test_scenario_description():
            assert test_description.__scenario__.feature.description == textwrap.dedent(
                \"\"\"\\
                In order to achieve something
                I want something
                Because it will be cool
                Given it is valid description
                When it starts working
                Then I will be happy


                Some description goes here.\"\"\"
            )
        """
        )
    )

    result = testdir.runpytest("-W ignore::pytest_bdd.FeatureWarning")
    result.assert_outcomes(passed=2)
