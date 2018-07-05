"""Test no scenarios defined in the feature file."""

import textwrap


def test_no_scenarios(testdir):
    """Test no scenarios defined in the feature file."""
    features = testdir.mkdir('features')
    features.join('test.feature').write_text(textwrap.dedent(u"""
        Given foo
        When bar
        Then baz
    """), 'utf-8', ensure=True)
    testdir.makepyfile(textwrap.dedent("""

        from pytest_bdd import scenarios

        scenarios('features')
    """))
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            '*FeatureError: Step definition outside of a Scenario or a Background.*',
        ],
    )


def test_only_background_strict_mode(testdir):
    """Test only wrong background defined in the feature file."""
    features = testdir.mkdir('features')
    features.join('test.feature').write_text(textwrap.dedent(u"""
    Background:
        Given foo
        When bar
    """), 'utf-8', ensure=True)
    testdir.makepyfile(textwrap.dedent("""

        from pytest_bdd import scenarios

        scenarios('features')
    """))
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            '*FeatureError: Background section can only contain Given steps.*',
        ],
    )
