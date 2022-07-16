import textwrap

from pytest_bdd.utils import collect_dumped_objects


def test_step_function_multiple_target_fixtures(testdir):
    testdir.makefile(
        ".feature",
        target_fixture=textwrap.dedent(
            """\
            Feature: Multiple target fixtures for step function
                Scenario: A step can be decorated multiple times with different target fixtures
                    Given there is a foo with value "test foo"
                    And there is a bar with value "test bar"
                    Then foo should be "test foo"
                    And bar should be "test bar"
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenarios, parsers
        from pytest_bdd.utils import dump_obj

        scenarios("target_fixture.feature")

        @given(parsers.parse('there is a foo with value "{value}"'), target_fixture="foo")
        @given(parsers.parse('there is a bar with value "{value}"'), target_fixture="bar")
        def _(value):
            return value

        @then(parsers.parse('foo should be "{expected_value}"'))
        def _(foo, expected_value):
            dump_obj(foo)
            assert foo == expected_value

        @then(parsers.parse('bar should be "{expected_value}"'))
        def _(bar, expected_value):
            dump_obj(bar)
            assert bar == expected_value
        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    [foo, bar] = collect_dumped_objects(result)
    assert foo == "test foo"
    assert bar == "test bar"


def test_step_override_caller_locals(testdir):
    testdir.makefile(
        ".feature",
        override_caller_locals=textwrap.dedent(
            """\
            Feature: Step decorators allow overriding caller_locals
                Scenario: I make my own step decorator that provides given, when, then steps
                    Given some data is loaded in the system
                    When some data is loaded in the system
                    Then some data is loaded in the system
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import sys

        import pytest
        from pytest_bdd import given, when, then, scenarios, parsers
        from pytest_bdd.utils import dump_obj

        scenarios("override_caller_locals.feature")

        global_counter = 0

        def step(*step_args, **step_kwargs):
            caller_locals = sys._getframe(1).f_locals
            def decorator(fn):
                @given(*step_args, **step_kwargs, caller_locals=caller_locals)
                @when(*step_args, **step_kwargs, caller_locals=caller_locals)
                @then(*step_args, **step_kwargs, caller_locals=caller_locals)
                def wrapper(*args, **kwargs):
                    return fn(*args, **kwargs)
                return wrapper
            return decorator

        @step("some data is loaded in the system", target_fixture="data")
        def _():
            global global_counter
            res = {"foo": global_counter}
            dump_obj(res)
            global_counter += 1
            return res

        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    dumped_objects = collect_dumped_objects(result)
    assert dumped_objects == [
        {"foo": 0},
        {"foo": 1},
        {"foo": 2},
    ]
