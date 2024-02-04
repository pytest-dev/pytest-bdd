import textwrap

import pytest

from pytest_bdd.utils import collect_dumped_objects


def test_steps(testdir):
    testdir.makefile(
        ".feature",
        # language=gherkin
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

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, when, then

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


def test_step_function_can_be_decorated_multiple_times(testdir, tmp_path):
    testdir.makeini(
        f"""\
        [pytest]
        bdd_features_base_dir={tmp_path}
        """
    )
    (tmp_path / "steps.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
            Feature: Steps decoration
                Scenario: Step function can be decorated multiple times
                    Given there is a foo with value 42
                    And there is a second foo with value 43
                    When I do nothing
                    And I do nothing again
                    Then I make no mistakes
                    And I make no mistakes again
            """,
        )
    )
    testdir.makepyfile(
        # language=python
        """\
        from pytest import fixture
        from pytest_bdd import given, when, then, scenario, parsers

        @fixture
        def first_foo():
            return 'first_foo'

        @fixture
        def second_foo():
            return 'second_foo'

        @given(parsers.parse("there is a foo with value {value}"), target_fixture="first_foo")
        @given(parsers.parse("there is a second foo with value {value}"), target_fixture="second_foo")
        def foo(value):
            yield value

        @when("I do nothing")
        @when("I do nothing again")
        def do_nothing(first_foo, second_foo):
            assert True

        @then("I make no mistakes")
        @then("I make no mistakes again")
        def no_errors(first_foo, second_foo):
            assert first_foo == '42'
            assert second_foo == '43'

        @scenario("steps.feature", "Step function can be decorated multiple times")
        def test_steps(
            first_foo,
            second_foo,
            request
        ):
            # Original fixture values are recieved from test parameters
            assert first_foo == 'first_foo'
            assert second_foo == 'second_foo'

            # Updated fixture values could be get from request fixture
            assert request.getfixturevalue('first_foo') == '42'
            assert request.getfixturevalue('second_foo') == '43'
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_all_steps_can_provide_fixtures(testdir):
    """Test that given/when/then can all provide fixtures."""
    testdir.makefile(
        ".feature",
        # language=gherkin
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

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, when, then, parsers

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
        # language=gherkin
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: When step can be the first
                    When I do nothing
                    Then I make no mistakes
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import when, then

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
        # language=gherkin
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: Then step can follow Given step
                    Given I have a foo fixture with value "foo"
                    Then foo should have value "foo"

            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, then

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


@pytest.mark.parametrize(
    "keyword",
    (
        "*",
        "And",
        "But",
    ),
)
def test_unknown_first(testdir, keyword):
    testdir.makefile(
        ".feature",
        # language=gherkin
        steps=f"""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: Then step can follow Given step
                    {keyword} I have a foo fixture with value "foo"
                    Then foo should have value "foo"

            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import step, then

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
        # language=gherkin
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
        # language=python
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
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_multiple_given(testdir):
    """Using the same given fixture raises an error."""
    testdir.makefile(
        ".feature",
        # language=gherkin
        steps="""\
            Feature: Steps are executed one by one
                Scenario: Using the same given twice
                    Given foo is "foo"
                    And foo is "bar"
                    Then foo should be "bar"

            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import parsers, given, then

        @given(parsers.parse("foo is {value}"), target_fixture="foo")
        def foo(value):
            return value

        @then(parsers.parse("foo should be {value}"))
        def foo_should_be(foo, value):
            assert foo == value
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1, failed=0)


def test_step_hooks(testdir):
    """When step fails."""
    testdir.makefile(
        ".feature",
        # language=gherkin
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
        # language=python
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
        # language=gherkin
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
        # language=python
        """\
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
        # language=gherkin
        steps="""\
            Feature: Steps parameters don't have to be passed as fixtures

                Scenario: StepHandler parameter don't have to be injected as fixture
                    Given I have a "foo" parameter which is not injected as fixture
                    Then parameter "foo" is not visible in fixtures

            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd.compatibility.pytest import FixtureLookupError
        from pytest import raises
        from pytest_bdd import given, then

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
        # language=gherkin
        steps="""\
            Feature: Steps parameters could be redirected to another fixture

                Scenario: Steps parameters could be redirected to another fixture
                    Given I have a "foo" parameter which is injected as fixture "bar"
                    Then fixture "bar" has value "foo"
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd.compatibility.pytest import FixtureLookupError
        from pytest import raises
        from pytest_bdd import given, then

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
        # language=gherkin
        steps="""\
            Feature: Steps parameters could be rejected at all to be injected as fixtures

                Scenario: Steps parameters could be rejected at all to be injected as fixtures
                    Given I have a "foo", "bar", "fizz", "buzz" parameters which are rejected by wild pattern
                    Then parameters "foo", "bar", "fizz", "buzz" are not visible in fixtures
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd.compatibility.pytest import FixtureLookupError
        from pytest import raises
        from pytest_bdd import given, then

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
        # language=gherkin
        steps="""\
            Feature: Steps parameters could be accepted at all to be injected as fixtures

                Scenario: Steps parameters could be accepted at all to be injected as fixtures
                    Given I have a "foo", "bar", "fizz", "buzz" parameters which are accepted by wild pattern
                    Then parameters "foo", "bar", "fizz", "buzz" are visible in fixtures
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, then

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
        # language=gherkin
        steps="""\
            Feature: Steps parameters could be accepted by wildcard and by list to be injected as fixtures

                Scenario: Steps parameters could be accepted by wildcard and by list to be injected as fixtures
                    Given I have a "foo", "bar", "fizz", "buzz" parameters few of which are accepted by wild pattern
                    Then parameters "fizz", "buzz" are visible in fixtures
                    Then parameters "cool_foo", "nice_bar" are visible in fixtures
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, then

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
        # language=gherkin
        a="""\
            Feature: A feature

                Scenario: A scenario
                    When I setup stuff
                    Then stuff should be 42
        """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import when, then

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


def test_liberal_step_decorator(testdir, tmp_path):
    testdir.makeini(
        f"""\
        [pytest]
        bdd_features_base_dir={tmp_path}
        """
    )
    (tmp_path / "steps.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
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
            """
        )
    )

    testdir.makepyfile(
        # language=python
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


def test_liberal_keyworded_step_decorator(testdir, tmp_path):
    testdir.makeini(
        f"""\
        [pytest]
        bdd_features_base_dir={tmp_path}
        """
    )
    (tmp_path / "steps.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
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
    )

    testdir.makepyfile(
        # language=python
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


def test_liberal_keyworded_step_decorator_cli_option(testdir, tmp_path):
    testdir.makeini(
        f"""\
        [pytest]
        bdd_features_base_dir={tmp_path}
        """
    )
    (tmp_path / "steps.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
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
    )

    testdir.makepyfile(
        # language=python
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


def test_liberal_keyworded_step_decorator_ini_option(testdir, tmp_path):
    testdir.makeini(
        f"""\
        [pytest]
        liberal_steps = True
        bdd_features_base_dir={tmp_path}
        """
    )

    (tmp_path / "steps.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
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
    )

    testdir.makepyfile(
        # language=python
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


def test_strict_step_has_precedence_over_liberal_step_decorator(testdir, tmp_path):
    testdir.makeini(
        f"""\
        [pytest]
        bdd_features_base_dir={tmp_path}
        """
    )
    (tmp_path / "steps.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
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
    )

    testdir.makepyfile(
        # language=python
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


def test_found_alternate_step_decorators_produce_warning(testdir, tmp_path):
    testdir.makeini(
        f"""\
        [pytest]
        bdd_features_base_dir={tmp_path}
        """
    )
    (tmp_path / "steps.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
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
    )

    testdir.makepyfile(
        # language=python
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
        # language=gherkin
        steps="""\
            Feature: Steps could be injected during run of other steps

                Scenario: Inject step from other step
                    When I inject step "Given" "I have foo"
                    Then I have foo
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from collections import deque

        from messages import PickleStep, Type
        from pytest_bdd import given, when, then

        @when("I inject step \\"{keyword}\\" \\"{step_text}\\"")
        def inject_step(steps_left: deque, keyword, step_text, scenario):
            steps_left.appendleft(PickleStep(
                id='MyStep',
                ast_node_ids=[],
                type=Type.context,
                text=step_text,
            ))

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
        # language=gherkin
        steps="""\
            Feature: Steps with default params

                Scenario: Step provides default_param
                    Given I have default defined param
                    Then I have foo
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given, then

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


def test_uses_correct_step_in_the_hierarchy(testdir, tmp_path):
    """
    Test regression found in issue #524, where we couldn't find the correct step implementation in the
    hierarchy of files/folder as expected.
    This test uses many files and folders that act as decoy, while the real step implementation is defined
    in the last file (test_b/test_b.py).
    """
    (tmp_path / "specific.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
            Feature: Specificity of steps
                Scenario: Overlapping steps
                    Given I have a specific thing
                    Then pass
            """
        )
    )

    testdir.makeconftest(
        textwrap.dedent(
            # language=python
            """\
            from pytest_bdd import parsers, given, then
            from pytest_bdd.utils import dump_obj

            @given(parsers.re("(?P<thing>.*)"))
            def root_conftest_catchall(thing):
                dump_obj(thing + " (catchall) root_conftest")

            @given(parsers.parse("I have a {thing} thing"))
            def root_conftest(thing):
                dump_obj(thing + " root_conftest")

            @given("I have a specific thing")
            def root_conftest_specific():
                dump_obj("specific" + "(specific) root_conftest")

            @then("pass")
            def _():
                pass
        """
        )
    )

    # Adding deceiving @when steps around the real test, so that we can check if the right one is used
    # the right one is the one in test_b/test_b.py
    # We purposefully use test_a and test_c as decoys (while test_b/test_b is "good one"), so that we can test that
    # we pick the right one.
    testdir.makepyfile(
        # language=python
        test_a="""\
            from pytest_bdd import given, parsers
            from pytest_bdd.utils import dump_obj

            @given(parsers.re("(?P<thing>.*)"))
            def in_root_test_a_catch_all(thing):
                dump_obj(thing + " (catchall) test_a")

            @given(parsers.parse("I have a specific thing"))
            def in_root_test_a_specific():
                dump_obj("specific" + " (specific) test_a")

            @given(parsers.parse("I have a {thing} thing"))
            def in_root_test_a(thing):
                dump_obj(thing + " root_test_a")
        """
    )
    testdir.makepyfile(
        # language=python
        test_c="""\
            from pytest_bdd import given, parsers
            from pytest_bdd.utils import dump_obj

            @given(parsers.re("(?P<thing>.*)"))
            def in_root_test_c_catch_all(thing):
                dump_obj(thing + " (catchall) test_c")

            @given(parsers.parse("I have a specific thing"))
            def in_root_test_c_specific():
                dump_obj("specific" + " (specific) test_c")

            @given(parsers.parse("I have a {thing} thing"))
            def in_root_test_c(thing):
                dump_obj(thing + " root_test_b")
        """
    )

    test_b_folder = testdir.mkpydir("test_b")

    # More decoys: test_b/test_a.py and test_b/test_c.py
    test_b_folder.join("test_a.py").write(
        textwrap.dedent(
            # language=python
            """\
                from pytest_bdd import given, parsers
                from pytest_bdd.utils import dump_obj

                @given(parsers.re("(?P<thing>.*)"))
                def in_root_test_b_test_a_catch_all(thing):
                    dump_obj(thing + " (catchall) test_b_test_a")

                @given(parsers.parse("I have a specific thing"))
                def in_test_b_test_a_specific():
                    dump_obj("specific" + " (specific) test_b_test_a")

                @given(parsers.parse("I have a {thing} thing"))
                def in_test_b_test_a(thing):
                    dump_obj(thing + " test_b_test_a")
            """
        )
    )
    test_b_folder.join("test_c.py").write(
        textwrap.dedent(
            # language=python
            """\
                from pytest_bdd import given, parsers
                from pytest_bdd.utils import dump_obj

                @given(parsers.re("(?P<thing>.*)"))
                def in_root_test_b_test_c_catch_all(thing):
                    dump_obj(thing + " (catchall) test_b_test_c")

                @given(parsers.parse("I have a specific thing"))
                def in_test_b_test_c_specific():
                    dump_obj("specific" + " (specific) test_a_test_c")

                @given(parsers.parse("I have a {thing} thing"))
                def in_test_b_test_c(thing):
                    dump_obj(thing + " test_c_test_a")
            """
        )
    )

    # Finally, the file with the actual step definition that should be used
    test_b_folder.join("test_b.py").write(
        textwrap.dedent(
            # language=python
            f"""\
                from pytest_bdd import scenarios, given, parsers
                from pytest_bdd.utils import dump_obj
                from pathlib import Path

                test_scenarios = scenarios(Path(r"{tmp_path}") / "specific.feature")

                @given(parsers.parse("I have a {{thing}} thing"))
                def in_test_b_test_b(thing):
                    dump_obj(f"{{thing}} test_b_test_b")
            """
        )
    )

    test_b_folder.join("test_b_alternative.py").write(
        textwrap.dedent(
            # language=python
            f"""\
            from pytest_bdd import scenarios, given, parsers
            from pytest_bdd.utils import dump_obj
            from pathlib import Path

            test_scenarios = scenarios(Path(r"{tmp_path}") /"specific.feature")

            # Here we try to use an argument different from the others,
            # to make sure it doesn't matter if a new step parser string is encountered.
            @given(parsers.parse("I have a {{t}} thing"))
            def in_test_b_test_b(t):
                dump_obj(f"{{t}} test_b_test_b")
            """
        )
    )

    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)

    [thing1, thing2] = collect_dumped_objects(result)
    assert thing1 == thing2 == "specific test_b_test_b"


def test_steps_parameters_injected_as_fixtures_are_not_shared_between_scenarios(testdir):
    testdir.makefile(
        ".feature",
        # language=gherkin
        steps="""\
            Feature: Steps parameters injected as fixtures are not shared between scenarios

                Scenario: Steps parameters injected as fixture
                    Given I have a "foo" parameter which is injected as fixture

                Scenario:
                    Then Fixture "foo" is inavailable
            """,
    )
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd.compatibility.pytest import FixtureLookupError
        from pytest import raises
        from pytest_bdd import given, then

        @given('I have a "{foo}" parameter which is injected as fixture')
        def inject_fixture(request):
            assert request.getfixturevalue('foo') == "foo"


        @then('Fixture "foo" is inavailable')
        def foo_is_foo(request):
            with raises(FixtureLookupError):
                request.getfixturevalue('foo')
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=2, failed=0)
