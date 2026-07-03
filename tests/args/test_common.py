from __future__ import annotations

import textwrap

from pytest_bdd.utils import collect_dumped_objects


def test_reuse_same_step_different_converters(pytester):
    pytester.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: Reuse same step with different converters
                Scenario: Step function should be able to be decorated multiple times with different converters
                    Given I have a foo with int value 42
                    And I have a foo with str value 42
                    And I have a foo with float value 42
                    When pass
                    Then pass
            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            r"""
        import pytest
        from pytest_bdd import parsers, given, when, then, scenarios
        from pytest_bdd.utils import dump_obj

        scenarios("arguments.feature")

        @given(parsers.re(r"^I have a foo with int value (?P<value>.*?)$"), converters={"value": int})
        @given(parsers.re(r"^I have a foo with str value (?P<value>.*?)$"), converters={"value": str})
        @given(parsers.re(r"^I have a foo with float value (?P<value>.*?)$"), converters={"value": float})
        def _(value):
            dump_obj(value)
            return value


        @then("pass")
        @when("pass")
        def _():
            pass
        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)

    [int_value, str_value, float_value] = collect_dumped_objects(result)
    assert type(int_value) is int
    assert int_value == 42

    assert type(str_value) is str
    assert str_value == "42"

    assert type(float_value) is float
    assert float_value == 42.0


def test_string_steps_dont_take_precedence(pytester):
    """Test that normal steps don't take precedence over the other steps."""
    pytester.makefile(
        ".feature",
        arguments=textwrap.dedent(
            """\
            Feature: Step precedence
                Scenario: String steps don't take precedence over other steps
                    Given I have a foo with value 42
                    When pass
                    Then pass
            """
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """
        from pytest_bdd import given, when, then, parsers
        from pytest_bdd.utils import dump_obj


        @given("I have a foo with value 42")
        def _():
            dump_obj("str")
            return 42


        @then("pass")
        @when("pass")
        def _():
            pass
        """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            r"""
        import pytest
        from pytest_bdd import parsers, given, when, then, scenarios
        from pytest_bdd.utils import dump_obj

        scenarios("arguments.feature")

        @given(parsers.re(r"^I have a foo with value (?P<value>.*?)$"))
        def _(value):
            dump_obj("re")
            return 42

        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)

    [which] = collect_dumped_objects(result)
    assert which == "re"
