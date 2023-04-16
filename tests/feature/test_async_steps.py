import textwrap


def test_steps(pytester):
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: Executed step by step
                    Given I have a foo fixture with value "foo"
                    And there is a list
                    When I append 1 to the list
                    And I append 2 to the list
                    And I append 3 to the list
                    Then foo should have value "foo"
                    But the list should be [1, 2, 3]
            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario
        from pytest_bdd.asyncio import async_given, async_when, async_then

        @scenario("steps.feature", "Executed step by step")
        def test_steps():
            pass

        @async_given('I have a foo fixture with value "foo"', target_fixture="foo")
        async def _():
            return "foo"


        @async_given("there is a list", target_fixture="results")
        async def _():
            yield []


        @async_when("I append 1 to the list")
        async def _(results):
            results.append(1)


        @async_when("I append 2 to the list")
        async def _(results):
            results.append(2)


        @async_when("I append 3 to the list")
        async def _(results):
            results.append(3)


        @async_then('foo should have value "foo"')
        async def _(foo):
            assert foo == "foo"


        @async_then("the list should be [1, 2, 3]")
        async def _(results):
            assert results == [1, 2, 3]

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_step_function_can_be_decorated_multiple_times(pytester):
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Steps decoration

                Scenario: Step function can be decorated multiple times
                    Given there is a foo with value 42
                    And there is a second foo with value 43
                    When I do nothing
                    And I do nothing again
                    Then I make no mistakes
                    And I make no mistakes again

            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario, parsers
        from pytest_bdd.asyncio import async_given, async_when, async_then

        @scenario("steps.feature", "Step function can be decorated multiple times")
        def test_steps():
            pass


        @async_given(parsers.parse("there is a foo with value {value}"), target_fixture="foo")
        @async_given(parsers.parse("there is a second foo with value {value}"), target_fixture="second_foo")
        async def _(value):
            return value


        @async_when("I do nothing")
        @async_when("I do nothing again")
        async def _():
            pass


        @async_then("I make no mistakes")
        @async_then("I make no mistakes again")
        async def _():
            assert True

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_all_steps_can_provide_fixtures(pytester):
    """Test that given/when/then can all provide fixtures."""
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Step fixture
                Scenario: Given steps can provide fixture
                    Given Foo is "bar"
                    Then foo should be "bar"
                Scenario: When steps can provide fixture
                    When Foo is "baz"
                    Then foo should be "baz"
                Scenario: Then steps can provide fixture
                    Then foo is "qux"
                    And foo should be "qux"
            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import parsers, scenarios
        from pytest_bdd.asyncio import async_given, async_when, async_then

        scenarios("steps.feature")

        @async_given(parsers.parse('Foo is "{value}"'), target_fixture="foo")
        async def _(value):
            return value


        @async_when(parsers.parse('Foo is "{value}"'), target_fixture="foo")
        async def _(value):
            return value


        @async_then(parsers.parse('Foo is "{value}"'), target_fixture="foo")
        async def _(value):
            return value


        @async_then(parsers.parse('foo should be "{value}"'))
        async def _(foo, value):
            assert foo == value

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=3, failed=0)


def test_when_first(pytester):
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: When step can be the first
                    When I do nothing
                    Then I make no mistakes
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import when, then, scenario
        from pytest_bdd.asyncio import async_when, async_then

        @scenario("steps.feature", "When step can be the first")
        def test_steps():
            pass

        @async_when("I do nothing")
        async def _():
            pass


        @async_then("I make no mistakes")
        async def _():
            assert True

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_then_after_given(pytester):
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: Then step can follow Given step
                    Given I have a foo fixture with value "foo"
                    Then foo should have value "foo"

            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario
        from pytest_bdd.asyncio import async_given, async_then

        @scenario("steps.feature", "Then step can follow Given step")
        def test_steps():
            pass

        @async_given('I have a foo fixture with value "foo"', target_fixture="foo")
        async def _():
            return "foo"

        @async_then('foo should have value "foo"')
        async def _(foo):
            assert foo == "foo"

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_conftest(pytester):
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: All steps are declared in the conftest
                    Given I have a bar
                    Then bar should have value "bar"

            """
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd.asyncio import async_given, async_then


        @async_given("I have a bar", target_fixture="bar")
        async def _():
            return "bar"


        @async_then('bar should have value "bar"')
        async def _(bar):
            assert bar == "bar"

        """
        )
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("steps.feature", "All steps are declared in the conftest")
        def test_steps():
            pass

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_multiple_given(pytester):
    """Using the same given fixture raises an error."""
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Steps are executed one by one
                Scenario: Using the same given twice
                    Given foo is "foo"
                    And foo is "bar"
                    Then foo should be "bar"

            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import parsers, scenario
        from pytest_bdd.asyncio import async_given, async_then


        @async_given(parsers.parse("foo is {value}"), target_fixture="foo")
        async def _(value):
            return value


        @async_then(parsers.parse("foo should be {value}"))
        async def _(foo, value):
            assert foo == value


        @scenario("steps.feature", "Using the same given twice")
        def test_given_twice():
            pass

        """
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_step_hooks(pytester):
    """When step fails."""
    pytester.makefile(
        ".feature",
        test="""
    Scenario: When step has hook on failure
        Given I have a bar
        When it fails

    Scenario: When step's dependency a has failure
        Given I have a bar
        When it's dependency fails

    Scenario: When step is not found
        Given not found

    Scenario: When step validation error happens
        Given foo
        And foo
    """,
    )
    pytester.makepyfile(
        """
        import pytest
        from pytest_bdd import scenario
        from pytest_bdd.asyncio import async_given, async_when

        @async_given('I have a bar')
        async def _():
            return 'bar'

        @async_when('it fails')
        async def _():
            raise Exception('when fails')

        @async_given('I have a bar')
        async def _():
            return 'bar'

        @pytest.fixture
        def dependency():
            raise Exception('dependency fails')

        @async_when("it's dependency fails")
        async def _(dependency):
            pass

        @scenario('test.feature', "When step's dependency a has failure")
        def test_when_dependency_fails():
            pass

        @scenario('test.feature', 'When step has hook on failure')
        def test_when_fails():
            pass

        @scenario('test.feature', 'When step is not found')
        def test_when_not_found():
            pass

        @async_when('foo')
        async def _():
            return 'foo'

        @scenario('test.feature', 'When step validation error happens')
        def test_when_step_validation_error():
            pass
    """
    )
    reprec = pytester.inline_run("-k test_when_fails")
    reprec.assertoutcome(failed=1)

    calls = reprec.getcalls("pytest_bdd_before_scenario")
    assert calls[0].request

    calls = reprec.getcalls("pytest_bdd_after_scenario")
    assert calls[0].request

    calls = reprec.getcalls("pytest_bdd_before_step")
    assert calls[0].request

    calls = reprec.getcalls("pytest_bdd_before_step_call")
    assert calls[0].request

    calls = reprec.getcalls("pytest_bdd_after_step")
    assert calls[0].request

    calls = reprec.getcalls("pytest_bdd_step_error")
    assert calls[0].request

    reprec = pytester.inline_run("-k test_when_not_found")
    reprec.assertoutcome(failed=1)

    calls = reprec.getcalls("pytest_bdd_step_func_lookup_error")
    assert calls[0].request

    reprec = pytester.inline_run("-k test_when_step_validation_error")
    reprec.assertoutcome(failed=1)

    reprec = pytester.inline_run("-k test_when_dependency_fails", "-vv")
    reprec.assertoutcome(failed=1)

    calls = reprec.getcalls("pytest_bdd_before_step")
    assert len(calls) == 2

    calls = reprec.getcalls("pytest_bdd_before_step_call")
    assert len(calls) == 1

    calls = reprec.getcalls("pytest_bdd_step_error")
    assert calls[0].request


def test_step_trace(pytester):
    """Test step trace."""
    pytester.makeini(
        """
        [pytest]
        console_output_style=classic
    """
    )

    pytester.makefile(
        ".feature",
        test="""
    Scenario: When step has failure
        Given I have a bar
        When it fails

    Scenario: When step is not found
        Given not found

    Scenario: When step validation error happens
        Given foo
        And foo
    """,
    )
    pytester.makepyfile(
        """
        import pytest
        from pytest_bdd import scenario
        from pytest_bdd.asyncio import async_given, async_when

        @async_given('I have a bar')
        async def _():
            return 'bar'

        @async_when('it fails')
        async def _():
            raise Exception('when fails')

        @scenario('test.feature', 'When step has failure')
        def test_when_fails_inline():
            pass

        @scenario('test.feature', 'When step has failure')
        def test_when_fails_decorated():
            pass

        @scenario('test.feature', 'When step is not found')
        def test_when_not_found():
            pass

        @async_when('foo')
        async def _():
            return 'foo'

        @scenario('test.feature', 'When step validation error happens')
        def test_when_step_validation_error():
            pass
    """
    )
    result = pytester.runpytest("-k test_when_fails_inline", "-vv")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*test_when_fails_inline*FAILED"])
    assert "INTERNALERROR" not in result.stdout.str()

    result = pytester.runpytest("-k test_when_fails_decorated", "-vv")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*test_when_fails_decorated*FAILED"])
    assert "INTERNALERROR" not in result.stdout.str()

    result = pytester.runpytest("-k test_when_not_found", "-vv")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*test_when_not_found*FAILED"])
    assert "INTERNALERROR" not in result.stdout.str()

    result = pytester.runpytest("-k test_when_step_validation_error", "-vv")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*test_when_step_validation_error*FAILED"])
    assert "INTERNALERROR" not in result.stdout.str()


def test_steps_with_yield(pytester):
    """Test that steps definition containing a yield statement work the same way as
    pytest fixture do, that is the code after the yield is executed during teardown."""

    pytester.makefile(
        ".feature",
        a="""\
Feature: A feature

    Scenario: A scenario
        When I setup stuff
        Then stuff should be 42
""",
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import scenarios
        from pytest_bdd.asyncio import async_when, async_then

        scenarios("a.feature")

        @async_when("I setup stuff", target_fixture="stuff")
        async def _():
            print("Setting up...")
            yield 42
            print("Tearing down...")


        @async_then("stuff should be 42")
        async def _(stuff):
            assert stuff == 42
            print("Asserted stuff is 42")

        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*Setting up...*",
            "*Asserted stuff is 42*",
            "*Tearing down...*",
        ]
    )
