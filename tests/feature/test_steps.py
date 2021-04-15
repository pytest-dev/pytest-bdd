import textwrap
import pytest


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
        def foo():
            return "foo"


        @given("there is a list", target_fixture="results")
        def results():
            return []


        @when("I append 1 to the list")
        def append_1(results):
            results.append(1)


        @when("I append 2 to the list")
        def append_2(results):
            results.append(2)


        @when("I append 3 to the list")
        def append_3(results):
            results.append(3)


        @then('foo should have value "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"


        @then("the list should be [1, 2, 3]")
        def check_results(results):
            assert results == [1, 2, 3]

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


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
        def do_nothing():
            pass


        @then("I make no mistakes")
        def no_errors():
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
        def foo():
            return "foo"

        @then('foo should have value "foo"')
        def foo_is_foo(foo):
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
        def bar():
            return "bar"


        @then('bar should have value "bar"')
        def bar_is_bar(bar):
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
        def foo(value):
            return value


        @then(parsers.parse("foo should be {value}"))
        def foo_should_be(foo, value):
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
        def i_have_bar():
            return 'bar'

        @when('it fails')
        def when_it_fails():
            raise Exception('when fails')

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        @pytest.fixture
        def dependency():
            raise Exception('dependency fails')

        @when("it's dependency fails")
        def when_dependency_fails(dependency):
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
        def foo():
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
        def i_have_bar():
            return 'bar'

        @when('it fails')
        def when_it_fails():
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
        def foo():
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
