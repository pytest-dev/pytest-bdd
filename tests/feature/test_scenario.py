"""Test scenario decorator."""
from textwrap import dedent

from pytest_bdd.compatibility.pytest import assert_outcomes


def test_simple(testdir, pytest_params, tmp_path):
    """Test scenario decorator with a standard usage."""
    (tmp_path / "simple.feature").write_text(
        dedent(
            # language=gherkin
            """\
            Feature: Simple feature
                Scenario: Simple scenario
                    Given I have a bar
            """,
        )
    )
    testdir.makepyfile(
        # language=python
        '''\
        from pathlib import Path

        from pytest_bdd import scenario, given, then

        @scenario(Path(r"'''
        f"{tmp_path / 'simple.feature'}"
        """"), "Simple scenario")
        def test_simple():
            pass

        @given("I have a bar")
        def bar():
            return "bar"

        @then("pass")
        def bar():
            pass
        """
    )
    result = testdir.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_scenario_not_found(testdir, pytest_params):
    """Test the situation when scenario is not found."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        not_found="""\
            Feature: Scenario is not found
            """,
    )
    result = testdir.runpytest_subprocess(*pytest_params)

    assert_outcomes(result, skipped=1)
