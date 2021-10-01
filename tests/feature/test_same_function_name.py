"""Function name same as step name."""

import textwrap

from _pytest.pytester import Testdir


def test_when_function_name_same_as_step_name(testdir: Testdir) -> None:
    testdir.makefile(
        ".feature",
        same_name=textwrap.dedent(
            """\
            Feature: Function name same as step name
                Scenario: When function name same as step name
                    When something
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import when, scenario

        @scenario("same_name.feature", "When function name same as step name")
        def test_same_name():
            pass

        @when("something")
        def something():
            return "something"
        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
