import textwrap


def test_steps(testdir):
    testdir.makefile(
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

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, scenario

        @scenario("steps.feature", "Executed step by step")
        def test_steps():
            pass

        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def _():
            return "foo"


        @given("there is a list", target_fixture="results")
        def _():
            return []


        @when("I append 1 to the list")
        def _(results):
            results.append(1)


        @when("I append 2 to the list")
        def _(results):
            results.append(2)


        @when("I append 3 to the list")
        def _(results):
            results.append(3)


        @then('foo should have value "foo"')
        def _(foo):
            assert foo == "foo"


        @then("the list should be [1, 2, 3]")
        def _(results):
            assert results == [1, 2, 3]

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_step_function_can_be_decorated_multiple_times(testdir):
    testdir.makefile(
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
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, scenario, parsers

        @scenario("steps.feature", "Step function can be decorated multiple times")
        def test_steps():
            pass


        @given(parsers.parse("there is a foo with value {value}"), target_fixture="foo")
        @given(parsers.parse("there is a second foo with value {value}"), target_fixture="second_foo")
        def _(value):
            return value


        @when("I do nothing")
        @when("I do nothing again")
        def _():
            pass


        @then("I make no mistakes")
        @then("I make no mistakes again")
        def _():
            assert True

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_all_steps_can_provide_fixtures(testdir):
    """Test that given/when/then can all provide fixtures."""
    testdir.makefile(
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

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, parsers, scenarios

        scenarios("steps.feature")

        @given(parsers.parse('Foo is "{value}"'), target_fixture="foo")
        def _(value):
            return value


        @when(parsers.parse('Foo is "{value}"'), target_fixture="foo")
        def _(value):
            return value


        @then(parsers.parse('Foo is "{value}"'), target_fixture="foo")
        def _(value):
            return value


        @then(parsers.parse('foo should be "{value}"'))
        def _(foo, value):
            assert foo == value

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=3, failed=0)


def test_when_first(testdir):
    testdir.makefile(
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
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import when, then, scenario

        @scenario("steps.feature", "When step can be the first")
        def test_steps():
            pass

        @when("I do nothing")
        def _():
            pass


        @then("I make no mistakes")
        def _():
            assert True

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_then_after_given(testdir):
    testdir.makefile(
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
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, then, scenario

        @scenario("steps.feature", "Then step can follow Given step")
        def test_steps():
            pass

        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def _():
            return "foo"

        @then('foo should have value "foo"')
        def _(foo):
            assert foo == "foo"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_conftest(testdir):
    testdir.makefile(
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
    testdir.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given, then


        @given("I have a bar", target_fixture="bar")
        def _():
            return "bar"


        @then('bar should have value "bar"')
        def _(bar):
            assert bar == "bar"

        """
        )
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("steps.feature", "All steps are declared in the conftest")
        def test_steps():
            pass

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_multiple_given(testdir):
    """Using the same given fixture raises an error."""
    testdir.makefile(
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
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import parsers, given, then, scenario


        @given(parsers.parse("foo is {value}"), target_fixture="foo")
        def _(value):
            return value


        @then(parsers.parse("foo should be {value}"))
        def _(foo, value):
            assert foo == value


        @scenario("steps.feature", "Using the same given twice")
        def test_given_twice():
            pass

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_step_hooks(testdir):
    """When step fails."""
    testdir.makefile(
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
    testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import given, when, scenario

        @given('I have a bar')
        def _():
            return 'bar'

        @when('it fails')
        def _():
            raise Exception('when fails')

        @given('I have a bar')
        def _():
            return 'bar'

        @pytest.fixture
        def dependency():
            raise Exception('dependency fails')

        @when("it's dependency fails")
        def _(dependency):
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

        @when('foo')
        def _():
            return 'foo'

        @scenario('test.feature', 'When step validation error happens')
        def test_when_step_validation_error():
            pass
    """
    )
    reprec = testdir.inline_run("-k test_when_fails")
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

    reprec = testdir.inline_run("-k test_when_not_found")
    reprec.assertoutcome(failed=1)

    calls = reprec.getcalls("pytest_bdd_step_func_lookup_error")
    assert calls[0].request

    reprec = testdir.inline_run("-k test_when_step_validation_error")
    reprec.assertoutcome(failed=1)

    reprec = testdir.inline_run("-k test_when_dependency_fails", "-vv")
    reprec.assertoutcome(failed=1)

    calls = reprec.getcalls("pytest_bdd_before_step")
    assert len(calls) == 2

    calls = reprec.getcalls("pytest_bdd_before_step_call")
    assert len(calls) == 1

    calls = reprec.getcalls("pytest_bdd_step_error")
    assert calls[0].request


def test_step_trace(testdir):
    """Test step trace."""
    testdir.makeini(
        """
        [pytest]
        console_output_style=classic
    """
    )

    testdir.makefile(
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
    testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import given, when, scenario

        @given('I have a bar')
        def _():
            return 'bar'

        @when('it fails')
        def _():
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

        @when('foo')
        def _():
            return 'foo'

        @scenario('test.feature', 'When step validation error happens')
        def test_when_step_validation_error():
            pass
    """
    )
    result = testdir.runpytest("-k test_when_fails_inline", "-vv")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*test_when_fails_inline*FAILED"])
    assert "INTERNALERROR" not in result.stdout.str()

    result = testdir.runpytest("-k test_when_fails_decorated", "-vv")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*test_when_fails_decorated*FAILED"])
    assert "INTERNALERROR" not in result.stdout.str()

    result = testdir.runpytest("-k test_when_not_found", "-vv")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*test_when_not_found*FAILED"])
    assert "INTERNALERROR" not in result.stdout.str()

    result = testdir.runpytest("-k test_when_step_validation_error", "-vv")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*test_when_step_validation_error*FAILED"])
    assert "INTERNALERROR" not in result.stdout.str()


def test_steps_with_yield(testdir):
    """Test that steps definition containing a yield statement work the same way as
    pytest fixture do, that is the code after the yield is executed during teardown."""

    testdir.makefile(
        ".feature",
        a="""\
Feature: A feature

    Scenario: A scenario
        When I setup stuff
        Then stuff should be 42
""",
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenarios

        scenarios("a.feature")

        @when("I setup stuff", target_fixture="stuff")
        def _():
            print("Setting up...")
            yield 42
            print("Tearing down...")


        @then("stuff should be 42")
        def _(stuff):
            assert stuff == 42
            print("Asserted stuff is 42")

        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)
    result.stdout.fnmatch_lines(
        [
            "*Setting up...*",
            "*Asserted stuff is 42*",
            "*Tearing down...*",
        ]
    )
