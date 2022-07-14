import pytest


def test_steps(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
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
            """,
    )

    testdir.makepyfile(
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
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_all_steps_can_provide_fixtures(testdir):
    """Test that given/when/then can all provide fixtures."""
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: StepHandler fixture
                Scenario: Given steps can provide fixture
                    Given Foo is "bar"
                    Then foo should be "bar"
                Scenario: When steps can provide fixture
                    When Foo is "baz"
                    Then foo should be "baz"
                Scenario: Then steps can provide fixture
                    Then foo is "qux"
                    And foo should be "qux"
            """,
    )

    testdir.makepyfile(
        """\
        from pytest_bdd import given, when, then, parsers, scenarios

        scenarios("steps.feature")

        @given(parsers.parse('Foo is "{value}"'), target_fixture="foo")
        def given_foo_is_value(value):
            return value


        @when(parsers.parse('Foo is "{value}"'), target_fixture="foo")
        def when_foo_is_value(value):
            return value


        @then(parsers.parse('Foo is "{value}"'), target_fixture="foo")
        def then_foo_is_value(value):
            return value


        @then(parsers.parse('foo should be "{value}"'))
        def foo_is_foo(foo, value):
            assert foo == value

        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=3, failed=0)


def test_when_first(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: When step can be the first
                    When I do nothing
                    Then I make no mistakes
            """,
    )
    testdir.makepyfile(
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
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_then_after_given(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: Then step can follow Given step
                    Given I have a foo fixture with value "foo"
                    Then foo should have value "foo"

            """,
    )
    testdir.makepyfile(
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
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_unknown_first(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: Then step can follow Given step
                    * I have a foo fixture with value "foo"
                    Then foo should have value "foo"

            """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd import step, then, scenario

        @scenario("steps.feature", "Then step can follow Given step")
        def test_steps():
            pass

        @step('I have a foo fixture with value "foo"', target_fixture="foo")
        def foo():
            return "foo"

        @then('foo should have value "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_conftest(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: All steps are declared in the conftest
                    Given I have a bar
                    Then bar should have value "bar"

            """,
    )
    testdir.makeconftest(
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
    testdir.makepyfile(
        """\
        from pytest_bdd import scenario

        @scenario("steps.feature", "All steps are declared in the conftest")
        def test_steps():
            pass
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_multiple_given(testdir):
    """Using the same given fixture raises an error."""
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Scenario: Using the same given twice
                    Given foo is "foo"
                    And foo is "bar"
                    Then foo should be "bar"

            """,
    )
    testdir.makepyfile(
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
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_step_hooks(testdir):
    """When step fails."""
    testdir.makefile(
        ".feature",
        test="""\
            Feature: StepHandler hooks
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
        """\
        import pytest
        from pytest_bdd import given, when, scenario

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        @when('it fails')
        def when_it_fails():
            raise Exception('when fails')

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
        test="""\
            Feature: Test step trace
                Scenario: When step has failure
                    Given I have a bar
                    When it fails

                Scenario: When step has failure inline
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
        """\
        import pytest
        from pytest_bdd import given, when, scenario

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        @when('it fails')
        def when_it_fails():
            raise Exception('when fails')

        test_when_fails_inline = scenario('test.feature', 'When step has failure inline', return_test_decorator=False)

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


def test_steps_parameter_mapping(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps parameters don't have to be passed as fixtures

                Scenario: StepHandler parameter don't have to be injected as fixture
                    Given I have a "foo" parameter which is not injected as fixture
                    Then parameter "foo" is not visible in fixtures

            """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd.typing.pytest import FixtureLookupError
        from pytest import raises
        from pytest_bdd import given, then, scenario

        @scenario("steps.feature", "StepHandler parameter don't have to be injected as fixture")
        def test_steps():
            pass

        @given('I have a "{foo}" parameter which is not injected as fixture', params_fixtures_mapping={})
        def foo(foo):
            assert foo == "foo"

        @then('parameter "foo" is not visible in fixtures')
        def foo_is_foo(request):
            with raises(FixtureLookupError):
                request.getfixturevalue('foo')
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_steps_parameter_mapping_could_redirect_to_fixture(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps parameters could be redirected to another fixture

                Scenario: Steps parameters could be redirected to another fixture
                    Given I have a "foo" parameter which is injected as fixture "bar"
                    Then fixture "bar" has value "foo"
            """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd.typing.pytest import FixtureLookupError
        from pytest import raises
        from pytest_bdd import given, then, scenario

        @scenario("steps.feature", "Steps parameters could be redirected to another fixture")
        def test_steps():
            pass

        @given('I have a "{foo}" parameter which is injected as fixture "bar"', params_fixtures_mapping={"foo":"bar"})
        def foo(foo, bar):
            assert foo == "foo"
            assert bar == "foo"

        @then('fixture "bar" has value "foo"')
        def foo_is_foo(request, bar):
            with raises(FixtureLookupError):
                request.getfixturevalue('foo')
            assert bar == "foo"
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


@pytest.mark.parametrize("mapping_string", ["{...: None}", "False", "()", "{}"])
def test_steps_parameter_mapping_rejection_for_all_parameters(testdir, mapping_string):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps parameters could be rejected at all to be injected as fixtures

                Scenario: Steps parameters could be rejected at all to be injected as fixtures
                    Given I have a "foo", "bar", "fizz", "buzz" parameters which are rejected by wild pattern
                    Then parameters "foo", "bar", "fizz", "buzz" are not visible in fixtures
            """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd.typing.pytest import FixtureLookupError
        from pytest import raises
        from pytest_bdd import given, then, scenario

        @scenario("steps.feature", "Steps parameters could be rejected at all to be injected as fixtures")
        def test_steps():
            pass

        @given('I have a "{foo}", "{bar}", "{fizz}", "{buzz}" parameters which are rejected by wild pattern',
               """
        f"""params_fixtures_mapping={mapping_string})"""
        """
        def foo(foo, bar, fizz, buzz):
            assert foo == "foo"
            assert bar == "bar"
            assert fizz == "fizz"
            assert buzz == "buzz"


        @then('parameters "foo", "bar", "fizz", "buzz" are not visible in fixtures')
        def foo_is_foo(request):
            with raises(FixtureLookupError):
                request.getfixturevalue('foo')
            with raises(FixtureLookupError):
                request.getfixturevalue('bar')
            with raises(FixtureLookupError):
                request.getfixturevalue('fizz')
            with raises(FixtureLookupError):
                request.getfixturevalue('buzz')
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


@pytest.mark.parametrize("mapping_string", ["{...: ...}", "True", "(...)"])
def test_steps_parameter_mapping_acceptance_for_all_parameters(testdir, mapping_string):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps parameters could be accepted at all to be injected as fixtures

                Scenario: Steps parameters could be accepted at all to be injected as fixtures
                    Given I have a "foo", "bar", "fizz", "buzz" parameters which are accepted by wild pattern
                    Then parameters "foo", "bar", "fizz", "buzz" are visible in fixtures
            """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd.typing.pytest import FixtureLookupError
        from pytest import raises
        from pytest_bdd import given, then, scenario

        @scenario("steps.feature", "Steps parameters could be accepted at all to be injected as fixtures")
        def test_steps():
            pass

        @given('I have a "{foo}", "{bar}", "{fizz}", "{buzz}" parameters which are accepted by wild pattern',
            """
        f"""params_fixtures_mapping={mapping_string})"""
        """
        def foo(foo, bar, fizz, buzz):
            assert foo == "foo"
            assert bar == "bar"
            assert fizz == "fizz"
            assert buzz == "buzz"


        @then('parameters "foo", "bar", "fizz", "buzz" are visible in fixtures')
        def foo_is_foo(foo, bar, fizz, buzz):
            assert foo == "foo"
            assert bar == "bar"
            assert fizz == "fizz"
            assert buzz == "buzz"
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_steps_parameter_mapping_acceptance_for_non_listed_parameters_by_wildcard(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps parameters could be accepted by wildcard and by list to be injected as fixtures

                Scenario: Steps parameters could be accepted by wildcard and by list to be injected as fixtures
                    Given I have a "foo", "bar", "fizz", "buzz" parameters few of which are accepted by wild pattern
                    Then parameters "fizz", "buzz" are visible in fixtures
                    Then parameters "cool_foo", "nice_bar" are visible in fixtures
            """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd.typing.pytest import FixtureLookupError
        from pytest import raises
        from pytest_bdd import given, then, scenario

        @scenario("steps.feature", "Steps parameters could be accepted by wildcard and by list to be injected as fixtures")
        def test_steps():
            pass

        @given('I have a "{foo}", "{bar}", "{fizz}", "{buzz}" parameters few of which are accepted by wild pattern',
               params_fixtures_mapping={'foo': 'cool_foo', 'bar': 'nice_bar', ...: ...})
        def foo(foo, bar, fizz, buzz, cool_foo, nice_bar):
            assert foo == "foo"
            assert bar == "bar"
            assert fizz == "fizz"
            assert buzz == "buzz"

            assert cool_foo == "foo"
            assert nice_bar == "bar"

        @then('parameters "fizz", "buzz" are visible in fixtures')
        def foo_is_foo(fizz, buzz):
            assert fizz == "fizz"
            assert buzz == "buzz"

        @then('parameters "cool_foo", "nice_bar" are visible in fixtures')
        def foo_is_foo(cool_foo, nice_bar):
            assert cool_foo == "foo"
            assert nice_bar == "bar"
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


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
        """\
        import pytest
        from pytest_bdd import given, when, then, scenarios

        scenarios("a.feature")

        @when("I setup stuff", target_fixture="stuff")
        def stuff():
            print("Setting up...")
            yield 42
            print("Tearing down...")


        @then("stuff should be 42")
        def check_stuff(stuff):
            assert stuff == 42
            print("Asserted stuff is 42")
        """
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


def test_liberal_step_decorator(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases. All steps could be
                executed by "step" decorator

                Scenario: Executed step by step
                    Given I execute foo step
                    And I execute bar step
                    When I execute fizz step
                    But I execute buzz step
                    Then I execute nice step
                    * I execute good step
            """,
    )

    testdir.makepyfile(
        """\
        from pytest_bdd import step, scenario
        from pytest import fixture

        @fixture
        def step_values():
            return []

        @scenario("steps.feature", "Executed step by step")
        def test_steps(step_values):
            assert "foo" in step_values
            assert "bar" in step_values
            assert "fizz" in step_values
            assert "buzz" in step_values
            assert "nice" in step_values
            assert "good" in step_values

        @step('I execute {value} step', liberal=True)
        def foo(step_values, value):
            step_values.append(value)
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_liberal_keyworded_step_decorator(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases. All steps could be
                executed by "step" decorator

                Scenario: Executed step by step
                    Given I execute foo step
                    And I execute bar step
                    When I execute fizz step
                    But I execute buzz step
                    Then I execute nice step
                    * I execute good step
            """,
    )

    testdir.makepyfile(
        """\
        from pytest_bdd import given, scenario
        from pytest import fixture

        @fixture
        def step_values():
            return []

        @scenario("steps.feature", "Executed step by step")
        def test_steps(step_values):
            assert "foo" in step_values
            assert "bar" in step_values
            assert "fizz" in step_values
            assert "buzz" in step_values
            assert "nice" in step_values
            assert "good" in step_values

        @given('I execute {value} step', liberal=True)
        def foo(step_values, value):
            step_values.append(value)
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_liberal_keyworded_step_decorator_cli_option(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases. All steps could be
                executed by "step" decorator

                Scenario: Executed step by step
                    Given I execute foo step
                    And I execute bar step
                    When I execute fizz step
                    But I execute buzz step
                    Then I execute nice step
                    * I execute good step
            """,
    )

    testdir.makepyfile(
        """\
        from pytest_bdd import given, scenario
        from pytest import fixture

        @fixture
        def step_values():
            return []

        @scenario("steps.feature", "Executed step by step")
        def test_steps(step_values):
            assert "foo" in step_values
            assert "bar" in step_values
            assert "fizz" in step_values
            assert "buzz" in step_values
            assert "nice" in step_values
            assert "good" in step_values

        @given('I execute {value} step')
        def foo(step_values, value):
            step_values.append(value)
        """
    )
    result = testdir.runpytest("--liberal-steps")
    result.assert_outcomes(passed=1, failed=0)


def test_liberal_keyworded_step_decorator_ini_option(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases. All steps could be
                executed by "step" decorator

                Scenario: Executed step by step
                    Given I execute foo step
                    And I execute bar step
                    When I execute fizz step
                    But I execute buzz step
                    Then I execute nice step
                    * I execute good step
            """,
    )

    testdir.makeini(
        """\
        [pytest]
        liberal_steps = True
        """
    )

    testdir.makepyfile(
        """\
        from pytest_bdd import given, scenario
        from pytest import fixture

        @fixture
        def step_values():
            return []

        @scenario("steps.feature", "Executed step by step")
        def test_steps(step_values):
            assert "foo" in step_values
            assert "bar" in step_values
            assert "fizz" in step_values
            assert "buzz" in step_values
            assert "nice" in step_values
            assert "good" in step_values

        @given('I execute {value} step')
        def foo(step_values, value):
            step_values.append(value)
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_strict_step_has_precedence_over_liberal_step_decorator(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases. All steps could be
                executed by "step" decorator

                Scenario: Executed step by step
                    Given I execute foo step
                    And I execute bar step
                    When I execute fizz step
                    But I execute buzz step
                    Then I execute nice step
                    * I execute good step
            """,
    )

    testdir.makepyfile(
        """\
        from pytest_bdd import given, when, step, scenario
        from pytest import fixture

        @fixture
        def liberal_step_values():
            return []

        @fixture
        def given_step_values():
            return []

        @fixture
        def when_step_values():
            return []

        @scenario("steps.feature", "Executed step by step")
        def test_steps(liberal_step_values, given_step_values, when_step_values):
            assert "foo" in given_step_values
            assert "bar" in given_step_values
            assert "fizz" in when_step_values
            assert "buzz" in when_step_values
            assert "nice" in liberal_step_values
            assert "good" in liberal_step_values

        @given('I execute {value} step')
        def foo(given_step_values, value):
            given_step_values.append(value)

        @step('I execute {value} step', liberal=True)
        def foo(liberal_step_values, value):
            liberal_step_values.append(value)

        @when('I execute {value} step', liberal=True)
        def foo(when_step_values, value):
            when_step_values.append(value)
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_found_alternate_step_decorators_produce_warning(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases. All steps could be
                executed by "step" decorator

                Scenario: Executed step by step
                    Given I execute foo step
                    And I execute bar step
                    When I execute fizz step
                    But I execute buzz step
                    Then I execute nice step
                    * I execute good step
            """,
    )

    testdir.makepyfile(
        """\
        from pytest_bdd import when, then, scenario
        from pytest import fixture

        @fixture
        def when_step_values():
            return []

        @fixture
        def then_step_values():
            return []

        @scenario("steps.feature", "Executed step by step")
        def test_steps(when_step_values, then_step_values,):
            assert "foo" in when_step_values or "foo" in then_step_values
            assert "bar" in when_step_values or "bar" in then_step_values
            assert "fizz" in when_step_values
            assert "buzz" in when_step_values
            assert "nice" in then_step_values
            assert "good" in then_step_values

        @when('I execute {value} step', liberal=True)
        def foo(when_step_values, value):
            when_step_values.append(value)

        @then('I execute {value} step', liberal=True)
        def foo(then_step_values, value):
            then_step_values.append(value)
        """
    )
    result = testdir.runpytest("-W", "ignore::pytest_bdd.PytestBDDStepDefinitionWarning")
    result.assert_outcomes(passed=1, failed=0)


def test_extend_steps_from_step(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps could be injected during run of other steps

                Scenario: Inject step from other step
                    When I inject step "Given" "I have foo"
                    Then I have foo
            """,
    )
    testdir.makepyfile(
        """\
        from collections import deque

        from pytest_bdd.model import UserStep
        from pytest_bdd import given, when, then, scenario

        @scenario("steps.feature", "Inject step from other step")
        def test_steps():
            pass

        @when("I inject step \\"{keyword}\\" \\"{step_text}\\"")
        def inject_step(steps_left: deque, keyword, step_text, scenario):
            steps_left.appendleft(UserStep(text=step_text, keyword=keyword, scenario=scenario))

        @given('I have {fixture_value}', target_fixture='foo_fixture')
        def save_fixture(fixture_value):
            return fixture_value

        @then("I have {fixture_value}")
        def check_fixture(fixture_value, foo_fixture):
            assert fixture_value == foo_fixture
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_default_params(testdir):
    testdir.makefile(
        ".feature",
        steps="""\
            Feature: Steps with default params

                Scenario: Step provides default_param
                    Given I have default defined param
                    Then I have foo
            """,
    )
    testdir.makepyfile(
        """\
        from pytest_bdd import given, then, scenario

        @scenario("steps.feature", "Step provides default_param")
        def test_steps():
            pass

        @given("I have default defined param", param_defaults={'default_param': 'foo'}, target_fixture='foo_fixture')
        def save_fixture(default_param):
            return default_param

        @then("I have {fixture_value}")
        def check_fixture(fixture_value, foo_fixture):
            assert fixture_value == foo_fixture
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)
