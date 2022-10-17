"""Test no scenarios defined in the feature file."""


def test_no_scenarios(testdir):
    """Test no scenarios defined in the feature file."""
    features = testdir.mkdir("features")
    features.join("test.feature").write_text(
        """\
        Given foo
        When bar
        Then baz
        """,
        "utf-8",
        ensure=True,
    )
    testdir.makepyfile(
        f"""\
        from pytest_bdd import scenarios
        from pytest_bdd.parser import GherkinParser as Parser

        scenarios('features', parser=Parser())
        """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(["*FeatureError*"])
