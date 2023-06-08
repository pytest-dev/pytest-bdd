"""Test wrong feature syntax."""

import textwrap

from pytest_bdd.compatibility.pytest import assert_outcomes


def test_multiple_features_single_file(testdir):
    """Test validation error when multiple features are placed in a single file."""
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            # language=gherkin
            """\
            Feature: Feature One

              Background:
                Given I have A
                And I have B

              Scenario: Do something with A
                When I do something with A
                Then something about B

            Feature: Feature Two

              Background:
                Given I have A

              Scenario: Something that just needs A
                When I do something else with A
                Then something else about B

              Scenario: Something that needs B again
                Given I have B
                When I do something else with B
                Then something else about A and B
        """
        ),
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines("*FeatureError: *")
