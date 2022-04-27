"""Function name same as step name."""

from pytest import mark, param


@mark.parametrize("parser,", [param("Parser", marks=[mark.deprecated]), "GherkinParser"])
def test_when_function_name_same_as_step_name(testdir, parser):
    testdir.makefile(
        ".feature",
        same_name="""\
            Feature: Function name same as step name
                Scenario: When function name same as step name
                    When something
            """,
    )
    testdir.makepyfile(
        f"""\
        from pytest_bdd import when, scenario
        from pytest_bdd.parser import {parser} as Parser

        @scenario("same_name.feature", "When function name same as step name", _parser=Parser())
        def test_same_name():
            pass

        @when("something")
        def something():
            return "something"
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
