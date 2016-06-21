"""Test no scenarios defined in the feature file."""

import py
import textwrap


def test_no_scenarios(testdir):
    """Test no scenarios defined in the feature file."""
    features = testdir.mkdir('features')
    features.join('test.feature').write_text(textwrap.dedent(u"""
        Given foo
        When bar
        Then baz
    """), 'utf-8', ensure=True)
    testdir.makepyfile(py.code.Source("""
        from pytest_bdd import scenarios

        scenarios('features')
    """))
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            '*FeatureError: Step definition outside of a Scenario or a Background.*',
        ],
    )
