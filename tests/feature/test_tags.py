"""Test tags."""
from operator import ge

from pytest_bdd.packaging import compare_distribution_version


def test_tags_selector(testdir):
    """Test tests selection by tags."""
    testdir.makefile(
        ".ini",
        pytest=
        # language=ini
        """\
            [pytest]
            markers =
                feature_tag_1
                feature_tag_2
                scenario_tag_01
                scenario_tag_02
                scenario_tag_10
                scenario_tag_20
            """,
    )
    testdir.makefile(
        ".feature",
        test=
        # language=gherkin
        """\
            @feature_tag_1 @feature_tag_2
            Feature: Tags

            @scenario_tag_01 @scenario_tag_02
            Scenario: Tags
                Given I have a bar

            @scenario_tag_10 @scenario_tag_20
            Scenario: Tags 2
                Given I have a bar
            """,
    )
    testdir.makepyfile(
        # language=python
        f"""\
        from pytest_bdd import given, scenarios

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        test_scenarios = scenarios('test.feature')
        """
    )
    result = testdir.runpytest("-m", "scenario_tag_10 and not scenario_tag_01", "-vv")
    outcomes = result.parseoutcomes()
    assert outcomes["passed"] == 1
    assert outcomes["deselected"] == 1

    result = testdir.runpytest("-m", "scenario_tag_01 and not scenario_tag_10", "-vv").parseoutcomes()
    assert result["passed"] == 1
    assert result["deselected"] == 1

    result = testdir.runpytest("-m", "feature_tag_1", "-vv").parseoutcomes()
    assert result["passed"] == 2

    result = testdir.runpytest("-m", "feature_tag_10", "-vv").parseoutcomes()
    assert result["deselected"] == 2


def test_tags_after_background_issue_160(testdir):
    """Make sure using a tag after background works."""
    testdir.makefile(
        ".ini",
        pytest=
        # language=ini
        """\
            [pytest]
            markers = tag
            """,
    )
    testdir.makefile(
        ".feature",
        test=
        # language=gherkin
        """\
            Feature: Tags after background

                Background:
                    Given I have a bar

                @tag
                Scenario: Tags
                    Given I have a baz

                Scenario: Tags 2
                    Given I have a baz
            """,
    )
    testdir.makepyfile(
        # language=python
        f"""\
        import pytest
        from pytest_bdd import given, scenarios

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        @given('I have a baz')
        def i_have_baz():
            return 'baz'

        test_scenarios = scenarios('test.feature')
        """
    )
    result = testdir.runpytest("-m", "tag", "-vv").parseoutcomes()
    assert result["passed"] == 1
    assert result["deselected"] == 1


def test_at_in_scenario(testdir):
    testdir.makefile(
        ".feature",
        test=
        # language=gherkin
        """\
            Feature: At sign in a scenario

                Scenario: Tags
                    Given I have a foo@bar

                Scenario: Second
                    Given I have a baz
            """,
    )
    testdir.makepyfile(
        # language=python
        f"""\
        from pytest_bdd import given, scenarios

        @given('I have a foo@bar')
        def i_have_at():
            return 'foo@bar'

        @given('I have a baz')
        def i_have_baz():
            return 'baz'

        test_scenarios = scenarios('test.feature')
    """
    )

    # Deprecate --strict after pytest 6.1
    # https://docs.org/en/stable/deprecations.html#the-strict-command-line-option
    strict_option = "--strict-markers" if compare_distribution_version("pytest", "6.2", ge) else "--strict"

    result = testdir.runpytest_subprocess(strict_option)
    result.stdout.fnmatch_lines(["*= 2 passed * =*"])


def test_invalid_tags(testdir):
    features = testdir.mkdir("features")
    features.join("test.feature").write_text(
        # language = gherkin
        """\
        Feature: Invalid tags
            Scenario: Invalid tags
                @tag
                Given foo
                When bar
                Then baz
        """,
        "utf-8",
        ensure=True,
    )
    testdir.makepyfile(
        # language = python
        f"""\
        from pytest_bdd import scenarios

        test_scenarios = scenarios('features')
        """
    )
    result = testdir.runpytest()
    result.stdout.fnmatch_lines(["*FeatureError*"])
