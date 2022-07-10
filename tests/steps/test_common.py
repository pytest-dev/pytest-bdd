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
