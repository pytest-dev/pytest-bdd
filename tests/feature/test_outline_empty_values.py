"""Scenario Outline with empty example values tests."""

import textwrap

from pytest_bdd.utils import collect_dumped_objects


def test_scenario_with_empty_example_values(pytester):
    pytester.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with empty example values
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    | #     |     |      |
            """
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """\
            from pytest_bdd import given, when, then, parsers
            from pytest_bdd.utils import dump_obj

            # Using `parsers.re` so that we can match empty values

            @given(parsers.re("there are (?P<start>.*?) cucumbers"))
            def _(start):
                dump_obj(start)


            @when(parsers.re("I eat (?P<eat>.*?) cucumbers"))
            def _(eat):
                dump_obj(eat)


            @then(parsers.re("I should have (?P<left>.*?) cucumbers"))
            def _(left):
                dump_obj(left)

            """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with empty example values")
        def test_outline():
            pass
        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)
    assert collect_dumped_objects(result) == ["#", "", ""]


def test_scenario_with_empty_example_values_none_transformer(pytester):
    """
    Checks that `parsers.re` can transform empty values to None with a converter.
    `parsers.parse` and `parsers.cfparse` won't work out of the box this way as they will fail to match the steps.
    """
    pytester.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with empty example values and transformer
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    | #     |     |      |
            """
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """\
            from pytest_bdd import given, when, then, parsers
            from pytest_bdd.utils import dump_obj


            def empty_to_none(value):
                return None if value.strip() == "" else value


            @given(parsers.re("there are (?P<start>.*?) cucumbers"), converters={"start": empty_to_none})
            def _(start):
                dump_obj(start)


            @when(parsers.re("I eat (?P<eat>.*?) cucumbers"), converters={"eat": empty_to_none})
            def _(eat):
                dump_obj(eat)


            @then(parsers.re("I should have (?P<left>.*?) cucumbers"), converters={"left": empty_to_none})
            def _(left):
                dump_obj(left)

            """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import scenario

            @scenario("outline.feature", "Outlined with empty example values and transformer")
            def test_outline():
                pass
            """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)
    assert collect_dumped_objects(result) == ["#", None, None]
