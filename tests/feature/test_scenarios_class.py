"""Tests for the ``scenarios_class`` class-returning API (Discussion #545)."""

from __future__ import annotations

import textwrap


def test_scenarios_class_collects_all_scenarios(pytester):
    """A class returned by ``scenarios_class`` is collected and runs every scenario."""
    pytester.makeconftest(
        """
        from pytest_bdd import given

        @given("I have a bar")
        def _():
            return "bar"
        """
    )
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: Class scenarios
                Scenario: First scenario
                    Given I have a bar

                Scenario: Second scenario
                    Given I have a bar
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios_class

        TestFeature = scenarios_class("features/test.feature")
        """
    )
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(["*TestFeature::test_first_scenario*", "*TestFeature::test_second_scenario*"])


def test_scenarios_class_subclass_can_override_one_scenario(pytester):
    """Subclassing the generated class lets a single scenario be overridden."""
    pytester.makeconftest(
        """
        from pytest_bdd import given

        @given("I have a bar")
        def _():
            return "bar"
        """
    )
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: Class scenarios
                Scenario: First scenario
                    Given I have a bar

                Scenario: Second scenario
                    Given I have a bar
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        """
        import pytest
        from pytest_bdd import scenario, scenarios_class

        class TestFeature(scenarios_class("features/test.feature")):
            # Override just the first scenario, e.g. to mark it as expected to fail,
            # while the rest keep running from the generated base class.
            @staticmethod
            @pytest.mark.xfail(reason="known issue")
            @scenario("features/test.feature", "First scenario")
            def test_first_scenario():
                raise AssertionError("boom")
        """
    )
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1, xfailed=1)


def test_scenarios_class_accepts_explicit_features_base_dir(pytester):
    """An explicit ``features_base_dir`` is honoured instead of being derived."""
    pytester.makeconftest(
        """
        from pytest_bdd import given

        @given("I have a bar")
        def _():
            return "bar"
        """
    )
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: Class scenarios
                Scenario: Only scenario
                    Given I have a bar
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        """
        import os

        from pytest_bdd import scenarios_class

        base_dir = os.path.join(os.path.dirname(__file__), "features")
        TestFeature = scenarios_class("test.feature", features_base_dir=base_dir)
        """
    )
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(["*TestFeature::test_only_scenario*"])


def test_scenarios_class_accepts_absolute_feature_path(pytester):
    """An absolute feature path is used as-is, without joining the base dir."""
    pytester.makeconftest(
        """
        from pytest_bdd import given

        @given("I have a bar")
        def _():
            return "bar"
        """
    )
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: Class scenarios
                Scenario: Only scenario
                    Given I have a bar
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        """
        import os

        from pytest_bdd import scenarios_class

        absolute_path = os.path.join(os.path.dirname(__file__), "features", "test.feature")
        TestFeature = scenarios_class(absolute_path)
        """
    )
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)


def test_scenarios_class_deduplicates_colliding_method_names(pytester):
    """Two distinct scenario names that map to one Python name get distinct methods."""
    pytester.makeconftest(
        """
        from pytest_bdd import given

        @given("I have a bar")
        def _():
            return "bar"
        """
    )
    features = pytester.mkdir("features")
    # "Do a thing" and "Do a thing!" are different scenarios but both normalise to
    # ``test_do_a_thing``, so the second must fall through to ``test_do_a_thing_1``.
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
            Feature: Class scenarios
                Scenario: Do a thing
                    Given I have a bar

                Scenario: Do a thing!
                    Given I have a bar
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios_class

        TestFeature = scenarios_class("features/test.feature")
        """
    )
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=2)
    result.stdout.fnmatch_lines(
        ["*TestFeature::test_do_a_thing*", "*TestFeature::test_do_a_thing_1*"]
    )


def test_scenarios_class_raises_when_no_scenarios_found(pytester):
    """A feature with no scenarios raises ``NoScenariosFound``."""
    features = pytester.mkdir("features")
    features.joinpath("empty.feature").write_text(
        textwrap.dedent(
            """
            Feature: No scenarios here
            """
        ),
        encoding="utf-8",
    )
    pytester.makepyfile(
        """
        import pytest

        from pytest_bdd import exceptions, scenarios_class


        def test_raises():
            with pytest.raises(exceptions.NoScenariosFound):
                scenarios_class("features/empty.feature")
        """
    )
    result = pytester.runpytest("-v")
    result.assert_outcomes(passed=1)
