def test_when_function_name_same_as_step_name(testdir):
    testdir.makefile(
        ".feature",
        # language=gherkin
        same_name="""\
            Feature: Function name same as step name
                Scenario: When function name same as step name
                    When something
            """,
    )
    testdir.makeconftest(
        # language=python
        f"""\
        from pytest_bdd import when

        @when("something")
        def something():
            return "something"
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
