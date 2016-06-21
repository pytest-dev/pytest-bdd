"""Test no scenarios defined in the feature file."""

<<<<<<< HEAD
import py
=======
>>>>>>> 887dac1... Better error explanation for the steps defined outside of scenarios
import textwrap


def test_no_scenarios(testdir):
    """Test no scenarios defined in the feature file."""
    features = testdir.mkdir('features')
    features.join('test.feature').write_text(textwrap.dedent(u"""
        Given foo
        When bar
        Then baz
    """), 'utf-8', ensure=True)
<<<<<<< HEAD
    testdir.makepyfile(py.code.Source("""
        from pytest_bdd import scenarios

        scenarios('features')
    """))
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(
        [
            '*FeatureError: Step definition outside of a Scenario or a Background.*',
=======
    testdir.makepyfile("""
        from pytest_bdd import scenarios

        scenarios('features')
    """)
    result = testdir.runpytest('-v', '-s')
    result.stdout.fnmatch_lines(
        [
            '*pytest_bdd.exceptions.FeatureError: Step definition outside of a Scenario or a Background.*',
>>>>>>> 887dac1... Better error explanation for the steps defined outside of scenarios
        ],
    )
