"""Scenario Outline with empty example values tests."""

from pytest_bdd.utils import collect_dumped_objects

STEPS = """\
    from pytest_bdd import given, when, then, parsers
    from pytest_bdd.utils import dump_obj

    # Using `parsers.re` so that we can match empty values

    @given(parsers.re("there are (?P<start>.*?) cucumbers"))
    def start_cucumbers(start):
        dump_obj(start)


    @when(parsers.re("I eat (?P<eat>.*?) cucumbers"))
    def eat_cucumbers(eat):
        dump_obj(eat)


    @then(parsers.re("I should have (?P<left>.*?) cucumbers"))
    def should_have_left_cucumbers(left):
        dump_obj(left)
"""


def test_scenario_with_empty_example_values(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Scenario Outline: Outlined with empty example values
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    | #     |     |      |
            """,
    )
    testdir.makeconftest(STEPS)

    testdir.makepyfile(
        f"""\
        from pytest_bdd import scenario
        from pytest_bdd.parser import GherkinParser as Parser

        @scenario("outline.feature", "Outlined with empty example values", parser=Parser())
        def test_outline():
            pass
        """
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)
    assert collect_dumped_objects(result) == ["#", "", ""]
