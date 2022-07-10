import textwrap

from pytest_bdd.utils import collect_dumped_objects


def test_reuse_same_step_different_converters(testdir):
    testdir.makefile(
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

    testdir.makepyfile(
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
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    [int_value, str_value, float_value] = collect_dumped_objects(result)
    assert type(int_value) is int
    assert int_value == 42

    assert type(str_value) is str
    assert str_value == "42"

    assert type(float_value) is float
    assert float_value == 42.0
