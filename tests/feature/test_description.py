"""Test descriptions."""

import textwrap


def test_description(pytester):
    """Test description for the feature."""
    pytester.makefile(
        ".feature",
        description=textwrap.dedent(
            """\
        Feature: Description

            In order to achieve something
            I want something
            Because it will be cool


            Some description goes here.

            Scenario: Description
                Also, the scenario can have a description.

                It goes here between the scenario name
                and the first step.
                Given I have a bar
        """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        import textwrap
        from pytest_bdd import given, scenario
        from pytest_bdd.scenario import scenario_wrapper_template_registry

        @scenario("description.feature", "Description")
        def test_description():
            pass


        @given("I have a bar")
        def _():
            return "bar"

        def test_feature_description():
            scenario = scenario_wrapper_template_registry[test_description]
            assert scenario.feature.description == textwrap.dedent(
                \"\"\"\\
                In order to achieve something
                I want something
                Because it will be cool


                Some description goes here.\"\"\"
            )

        def test_scenario_description():
            scenario = scenario_wrapper_template_registry[test_description]
            assert scenario.description == textwrap.dedent(
                \"\"\"\\
                Also, the scenario can have a description.

                It goes here between the scenario name
                and the first step.\"\"\"
            )
        """
        )
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=3)
