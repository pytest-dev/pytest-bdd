from __future__ import annotations

import textwrap


def test_multiple_features_error(pytester):
    """Test multiple features in a single feature file."""
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: First Feature
                Scenario: First Scenario
                    Given a step

            Feature: Second Feature
                Scenario: Second Scenario
                    Given another step
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
            from pytest_bdd import scenarios

            scenarios('features')
            """
        )
    )

    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*FeatureError: Multiple features are not allowed in a single feature file.*"])


def test_step_outside_scenario_or_background_error(pytester):
    """Test step outside of a Scenario or Background."""
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: Invalid Feature
            # Step not inside a scenario or background
            Given a step that is not inside a scenario or background

                Scenario: A valid scenario
                    Given a step inside a scenario

            """
        ),
        encoding="utf-8",
    )

    pytester.makepyfile(
        textwrap.dedent(
            """
            from pytest_bdd import scenarios, given

            @given("a step inside a scenario")
            def step_inside_scenario():
                pass

            scenarios('features')
            """
        )
    )

    result = pytester.runpytest()

    # Expect the FeatureError for the step outside of scenario or background
    result.stdout.fnmatch_lines(["*FeatureError: Step definition outside of a Scenario or a Background.*"])


def test_multiple_backgrounds_error(pytester):
    """Test multiple backgrounds in a single feature."""
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: Feature with multiple backgrounds
                Background: First background
                    Given a first background step

                Background: Second background
                    Given a second background step

                Scenario: A valid scenario
                    Given a step in the scenario
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
            from pytest_bdd import scenarios

            scenarios('features')
            """
        )
    )

    result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        ["*BackgroundError: Multiple 'Background' sections detected. Only one 'Background' is allowed per feature.*"]
    )


def test_misplaced_scenario_error(pytester):
    """Test misplaced or incorrect Scenario keywords."""
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Scenario: First scenario
                Given a step

            Scenario: Misplaced scenario
                Given another step
                When I have something wrong
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
            from pytest_bdd import scenarios, given, when

            @given("a step")
            def a_step():
                pass

            @given("another step")
            def another_step():
                pass

            @when("I have something wrong")
            def something_wrong():
                pass

            scenarios('features')
            """
        )
    )

    result = pytester.runpytest()

    # Expect that no ScenarioError will actually be raised here
    result.stdout.fnmatch_lines(
        [
            "*ScenarioError: Misplaced or incorrect 'Scenario' keyword. Ensure it's correctly placed. There might be a missing Feature section.*"
        ]
    )


def test_misplaced_rule_error(pytester):
    """Test misplaced or incorrectly formatted Rule."""
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Rule: Misplaced rule
                Feature: Feature with misplaced rule
                    Scenario: A scenario inside a rule
                    Given a step
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
            from pytest_bdd import given, scenarios

            scenarios('features')

            @given("a step")
            def a_step():
                pass
            """
        )
    )

    result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        ["*RuleError: Misplaced or incorrectly formatted 'Rule'. Ensure it follows the feature structure.*"]
    )


def test_improper_step_error(pytester):
    """Test improper step without keyword."""
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: Feature with improper step
                Scenario: Scenario with improper step
                    Given a valid step
                    InvalidStep I have an invalid step
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
            from pytest_bdd import scenarios

            scenarios('features')
            """
        )
    )

    result = pytester.runpytest()
    result.stdout.fnmatch_lines(["*TokenError: Unexpected token found. Check Gherkin syntax near the reported error.*"])


def test_improper_initial_keyword(pytester):
    """Test first step using incorrect initial keyword."""
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: Incorrect initial keyword

            Scenario: No initial Given, When or Then
                And foo
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        textwrap.dedent(
            """
            from pytest_bdd import given, scenarios

            scenarios('features')

            @given("foo")
            def foo():
                pass

            @then("bar")
            def bar():
                pass
            """
        )
    )

    result = pytester.runpytest()
    result.stdout.fnmatch_lines(
        ["*StepError: First step in a scenario or background must start with 'Given', 'When' or 'Then', but got And.*"]
    )
