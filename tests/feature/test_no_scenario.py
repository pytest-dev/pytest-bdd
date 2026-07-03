"""Test no scenarios defined in the feature file."""

from __future__ import annotations

import textwrap


def test_no_scenarios(pytester):
    """Test no scenarios defined in the feature file."""
    features = pytester.mkdir("features")
    features.joinpath("test.feature").write_text(
        textwrap.dedent(
            """
        Given foo
        When bar
        Then baz
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
    result.stdout.fnmatch_lines(["*FeatureError: Step definition outside of a Scenario or a Background.*"])
