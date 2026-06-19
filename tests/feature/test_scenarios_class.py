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
