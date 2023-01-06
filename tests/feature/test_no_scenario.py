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
        # language=python
        f"""\
        from pytest_bdd import scenarios

        test_cukes = scenarios('features')
        """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(["*FeatureError*"])
