"""Scenario Outline tests."""
import textwrap

import pytest

from pytest_bdd.utils import collect_dumped_objects
from tests.utils import assert_outcomes

STEPS = """\
from pytest_bdd import parsers, given, when, then
from pytest_bdd.utils import dump_obj


@given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
def start_cucumbers(start):
    assert isinstance(start, int)
    dump_obj(start)
    return {"start": start}


@when(parsers.parse("I eat {eat:g} cucumbers"))
def eat_cucumbers(start_cucumbers, eat):
    assert isinstance(eat, float)
    dump_obj(eat)
    start_cucumbers["eat"] = eat


@then(parsers.parse("I should have {left} cucumbers"))
def should_have_left_cucumbers(start_cucumbers, start, eat, left):
    assert isinstance(left, str)
    dump_obj(left)
    assert start - eat == int(left)
    assert start_cucumbers["start"] == start
    assert start_cucumbers["eat"] == eat

"""
STEPS_OUTLINED = """\
    from pytest_bdd import given, when, then, scenario, parsers
    from pytest_bdd.utils import dump_obj
    from pytest_bdd.parser import Parser

    @scenario(
        "outline.feature",
        "Outlined given, when, thens",
        _parser=Parser()
    )
    def test_outline():
        pass

    @given(parsers.parse("there are {start:d} {fruits}"), target_fixture="start_fruits")
    def start_fruits(start, fruits):
        dump_obj(start, fruits)

        assert isinstance(start, int)
        return {fruits: dict(start=start)}


    @when(parsers.parse("I eat {eat:g} {fruits}"))
    def eat_fruits(start_fruits, eat, fruits):
        dump_obj(eat, fruits)

        assert isinstance(eat, float)
        start_fruits[fruits]["eat"] = eat


    @then(parsers.parse("I should have {left} {fruits}"))
    def should_have_left_fruits(start_fruits, start, eat, left, fruits):
        dump_obj(left, fruits)

        assert isinstance(left, str)
        assert start - eat == int(left)
        assert start_fruits[fruits]["start"] == start
        assert start_fruits[fruits]["eat"] == eat
"""


@pytest.mark.parametrize(
    "examples_header",
    (
        pytest.param("Examples:", id="non_named"),
        pytest.param("Examples: Named", id="named"),
    ),
)
def test_outlined(testdir, examples_header):
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            f"""\
            Feature: Outline
                Scenario Outline: Outlined given, when, thens
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    {examples_header}
                    | start | eat | left |
                    |  12   |  5  |  7   | # a comment
                    |  5    |  4  |  1   |

            """
        ),
    )

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
        )
        def test_outline(request):
            pass

        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)
    # fmt: off
    assert collect_dumped_objects(result) == [
        12, 5.0, "7",
        5, 4.0, "1",
    ]
    # fmt: on


@pytest.mark.xfail(reason="https://github.com/cucumber/common/issues/1953")
def test_wrongly_outlined_duplicated_parameter_scenario(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with duplicated parameter example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | start | left |
                    |   12  |   10  |   7  |
                    |    2  |    1  |   1  |
            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with wrong vertical example table")
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        "*Scenario has not valid examples. Example rows should contain unique parameters. "
        '"start" appeared more than once.*'
    )


def test_wrongly_outlined_missing_parameter_scenario(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    |   12  | 10  |   7  |
                    |    2  |  1  |
            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with wrong vertical example table")
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines("*FeatureError*")


@pytest.mark.deprecated
def test_wrongly_outlined_duplicated_parameter_feature(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Examples:
                 | start | start | left |
                 |   12  |   10  |   7  |
                 |    2  |    1  |   1  |

                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers
            """,
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        """\
        from pytest_bdd import scenario
        from pytest_bdd.parser import Parser

        @scenario("outline.feature", "Outlined with wrong vertical example table", _parser=Parser())
        def test_outline(request):
            pass
        """
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        "*Feature has not valid examples. Example rows should contain unique parameters. "
        '"start" appeared more than once.*'
    )


def test_outlined_with_other_fixtures(testdir):
    """Test outlined scenario also using other parametrized fixture."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined given, when, thens
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   |
                    |  5    |  4  |  1   |

            """
        ),
    )

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import scenario


        @pytest.fixture(params=[1, 2, 3])
        def other_fixture(request):
            return request.param


        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
        )
        def test_outline(other_fixture):
            pass

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=6)


@pytest.mark.deprecated
@pytest.mark.parametrize(
    "examples_header",
    (
        pytest.param("Examples: Vertical", id="non_named"),
        pytest.param("Examples: Vertical Named", id="named"),
    ),
)
def test_vertical_example(testdir, examples_header):
    """Test outlined scenario with vertical examples table."""
    testdir.makefile(
        ".feature",
        outline=f"""\
            Feature: Outline
                Scenario Outline: Outlined with vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    {examples_header}
                    | start | 12 | 2 | # a comment
                    | eat   | 5  | 1 |
                    | left  | 7  | 1 |
        """,
    )

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        """\
        from pytest_bdd import scenario
        from pytest_bdd.parser import Parser

        @scenario(
            "outline.feature",
            "Outlined with vertical example table",
            _parser=Parser()
        )
        def test_outline():
            pass
        """
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, 5.0, "7",
        2, 1.0, "1",
    ]
    # fmt: on


@pytest.mark.deprecated
def test_wrongly_outlined_duplicated_parameter_vertical_scenario(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples: Vertical
                    | start | 12 | 2 |
                    | start | 10 | 1 |
                    | left  | 7  | 1 |
        """,
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        """\
        from pytest_bdd import scenario
        from pytest_bdd.parser import Parser

        @scenario("outline.feature", "Outlined with wrong vertical example table", _parser=Parser())
        def test_outline(request):
            pass
        """
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        "*Scenario has not valid examples. Example rows should contain unique parameters. "
        '"start" appeared more than once.*'
    )


@pytest.mark.deprecated
def test_wrongly_outlined_missing_parameter_vertical_scenario(testdir):
    """Test parametrized scenario vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples: Vertical
                    | start | 12 | 2 |
                    | eat   | 10 | 1 |
                    | left  | 7  |
            """,
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        """\
        from pytest_bdd import scenario
        from pytest_bdd.parser import Parser

        @scenario("outline.feature", "Outlined with wrong vertical example table", _parser=Parser())
        def test_outline(request):
            pass
        """
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        "*Scenario has not valid examples. All example columns in Examples: Vertical must have same count of values.*"
    )


@pytest.mark.deprecated
def test_wrongly_outlined_duplicated_parameter_vertical_feature(testdir):
    """Test parametrized feature vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outlines

                Examples: Vertical
                | start | 12 | 2 |
                | start | 10 | 1 |
                | left  | 7  | 1 |

                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers
            """,
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        """\
        from pytest_bdd import scenario
        from pytest_bdd.parser import Parser

        @scenario("outline.feature", "Outlined with wrong vertical example table", _parser=Parser())
        def test_outline(request):
            pass
        """
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        "*Feature has not valid examples. Example rows should contain unique parameters. "
        '"start" appeared more than once.*'
    )


@pytest.mark.deprecated
def test_outlined_feature(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:
                | start | eat | left |
                |  12   |  5  |  7   |
                |  5    |  4  |  1   |

                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | fruits  |
                    | oranges |
                    | apples  |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=4)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, "oranges", 5.0, "oranges", "7", "oranges",
        12, "apples", 5.0, "apples", "7", "apples",
        5, "oranges", 4.0, "oranges", "1", "oranges",
        5, "apples", 4.0, "apples", "1", "apples",
    ]
    # fmt: on


@pytest.mark.xfail(reason="https://github.com/cucumber/common/issues/1954")
def test_outline_with_escaped_pipes(testdir):
    """Test parametrized feature example table with escaped pipe characters in input."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            r"""\
            Feature: Outline With Special characters

                Scenario Outline: Outline with escaped pipe character
                    # Just print the string so that we can assert later what it was by reading the output
                    Given I print the <string>

                    Examples:
                    | string       |
                    | bork         |
                    | \|bork       |
                    | bork \|      |
                    | bork\|\|bork |
                    | \|           |
                    | bork      \\ |
                    | bork    \\\| |
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import scenario, given, parsers
            from pytest_bdd.utils import dump_obj


            @scenario("outline.feature", "Outline with escaped pipe character")
            def test_outline_with_escaped_pipe_character(request):
                pass


            @given(parsers.parse("I print the {string}"))
            def i_print_the_string(string):
                dump_obj(string)
            """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=7)
    assert collect_dumped_objects(result) == [
        r"bork",
        r"|bork",
        r"bork |",
        r"bork||bork",
        r"|",
        r"bork      \\",
        r"bork    \\|",
    ]


@pytest.mark.deprecated
def test_multi_outlined(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Scenario Outline: Outlined given, when, thens
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   | # a comment

                    Examples: Vertical
                    | start | 5 |
                    | eat   | 4 |
                    | left  | 1 |
            """,
    )

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        """\
        from pytest_bdd import scenario
        from pytest_bdd.parser import Parser

        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
            _parser=Parser(),
        )
        def test_outline(request):
            pass
        """
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)
    # fmt: off
    assert collect_dumped_objects(result) == [
        12, 5.0, "7",
        5, 4.0, "1",
    ]
    # fmt: on


@pytest.mark.deprecated
def test_multi_outlined_empty_examples(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:

                Examples: Vertical

                Examples:
                |

                Examples: Vertical
                |

                Scenario Outline: Outlined given, when, thens
                    Given there are 12 apples
                    When I eat 5 apples
                    Then I should have 7 apples

                    Examples:

                    Examples: Vertical

                    Examples:
                    |

                    Examples: Vertical
                    |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=16)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == 16 * [
        12, "apples", 5.0, "apples", "7", "apples",
    ]
    # fmt: on


@pytest.mark.deprecated
def test_multi_outlined_tagged_empty_examples(testdir):
    testdir.makefile(
        ".ini",
        pytest="""\
            [pytest]
            markers =
                cool_tag
                nice_tag
            """,
    )

    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:

                Examples: Vertical

                Examples:
                |@       |
                |nice_tag|

                Examples: Vertical
                |

                Scenario Outline: Outlined given, when, thens
                    Given there are 12 apples
                    When I eat 5 apples
                    Then I should have 7 apples

                    Examples:

                    @cool_tag
                    Examples: Vertical

                    Examples:
                    |

                    Examples: Vertical
                    |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s", "-m", "cool_tag and nice_tag")
    result.assert_outcomes(passed=1)
    result = testdir.runpytest("-s", "-m", "cool_tag or nice_tag")
    result.assert_outcomes(passed=7)


@pytest.mark.deprecated
def test_multi_outlined_feature_with_parameter_union(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:
                | start | eat | left |
                |  12   |  5  |  7   |

                Examples: Vertical
                | start | 5 |
                | eat   | 4 |
                | left  | 1 |

                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | fruits  |
                    | oranges |
                    | apples  |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=4)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, "oranges", 5.0, "oranges", "7", "oranges",
        12, "apples", 5.0, "apples", "7", "apples",
        5, "oranges", 4.0, "oranges", "1", "oranges",
        5, "apples", 4.0, "apples", "1", "apples",
    ]
    # fmt: on


@pytest.mark.deprecated
def test_multi_outlined_scenario_and_feature_with_parameter_union(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:
                | start | eat | left |
                |  12   |  5  |  7   |

                Examples: Vertical
                | start | 5 |
                | eat   | 4 |
                | left  | 1 |

                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples: Vertical
                    | fruits | oranges |

                    Examples:
                    | fruits  |
                    | apples  |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=4)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, "oranges", 5.0, "oranges", "7", "oranges",
        12, "apples", 5.0, "apples", "7", "apples",
        5, "oranges", 4.0, "oranges", "1", "oranges",
        5, "apples", 4.0, "apples", "1", "apples",
    ]
    # fmt: on


@pytest.mark.deprecated
def test_outlined_scenario_and_feature_with_parameter_join_by_one_parameter(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:
                | start | eat | left |
                |  12   |  5  |  7   |
                |   5   |  4  |  1   |


                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | fruits  | left |
                    | apples  |  7   |
                    | oranges |  1   |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, "apples", 5.0, "apples", "7", "apples",
        5, "oranges", 4.0, "oranges", "1", "oranges",
    ]
    # fmt: on


@pytest.mark.deprecated
def test_outlined_scenario_and_feature_with_parameter_join_by_multi_parameter(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:
                | fruits    | start | eat | left |
                | apples    |  12   |  5  |  7   |
                | apples    |  12   |  9  |  3   |  # not joined by <eat> <left>
                | oranges   |   5   |  4  |  1   |
                | cucumbers |   8   |  3  |  5   |  # not joined by <eat> <left>


                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | fruits    | eat | left |
                    | apples    |  5  |  7   |
                    | oranges   |  4  |  1   |
                    | cucumbers |  5  |  7   |  # not joined by <fruits>
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, "apples", 5.0, "apples", "7", "apples",
        5, "oranges", 4.0, "oranges", "1", "oranges",
    ]
    # fmt: on


@pytest.mark.deprecated
def test_outlined_scenario_and_feature_with_parameter_join_empty_and_non_empty_parameter_1(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:
                | fruits    | start | eat | left |
                | apples    |  12   |  5  |  7   |
                | apples    |  12   |  9  |  3   |
                | oranges   |   5   |  4  |  1   |
                | cucumbers |   8   |  3  |  5   |


                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=4)


@pytest.mark.deprecated
def test_outlined_scenario_and_feature_with_parameter_join_empty_and_non_empty_parameter_2(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:
                |


                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | fruits    | start | eat | left |
                    | apples    |  12   |  5  |  7   |
                    | apples    |  12   |  9  |  3   |
                    | oranges   |   5   |  4  |  1   |
                    | cucumbers |   8   |  3  |  5   |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=4)


@pytest.mark.deprecated
def test_outlined_scenario_and_feature_with_parameter_join_by_external_parameter(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline

                Examples:
                | fruits    | start | eat | external |
                | apples    |  12   |  5  |     a    |
                | oranges   |   5   |  4  |     b    |
                | cucumbers |   8   |  3  |     c    | # not joined by <external>


                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | left | external |
                    |  7   |     a    |
                    |  1   |     b    |
                    |  4   |     d    | # not joined by <external>
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, "apples", 5.0, "apples", "7", "apples",
        5, "oranges", 4.0, "oranges", "1", "oranges",
    ]
    # fmt: on


@pytest.mark.deprecated
def test_outlined_scenario_and_feature_with_parameter_join_by_multi_parameter_unbalanced(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Examples:
                | start | eat | left |
                |  14   |  6  |  8   |
                |  15   |  5  |  10  |

                Examples:
                | fruits    | start | eat | left |
                | apples    |  12   |  5  |  7   |
                | apples    |  12   |  9  |  3   |
                | oranges   |   5   |  4  |  1   |
                | cucumbers |   8   |  3  |  5   |


                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | fruits    | eat | left |
                    | apples    |  5  |  7   |
                    | oranges   |  4  |  1   |
                    | cucumbers |  5  |  7   |

                    Examples:
                    | fruits     |
                    | pineapples |
                    | peaches    |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=6)
    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        14, 'pineapples', 6.0, 'pineapples', '8', 'pineapples',
        14, 'peaches', 6.0, 'peaches', '8', 'peaches',
        15, 'pineapples', 5.0, 'pineapples', '10', 'pineapples',
        15, 'peaches', 5.0, 'peaches', '10', 'peaches',
        12, 'apples', 5.0, 'apples', '7', 'apples',
        5, 'oranges', 4.0, 'oranges', '1', 'oranges'
    ]
    # fmt: on


@pytest.mark.deprecated
def test_outlined_scenario_and_feature_with_insufficient_parameter_join(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Examples:
                | fruits    |
                | apples    |
                | oranges   |

                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | eat | left |
                    |  5  |  7   |
                    |  4  |  1   |

                    Examples:
                    | fruits     | start |
                    | pineapples |   12  |
                    | peaches    |   10  |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest(
        "-s",
        "-W ignore::pytest_bdd.PytestBDDScenarioExamplesExtraParamsWarning",
        "-W ignore::pytest_bdd.PytestBDDScenarioStepsExtraPramsWarning",
    )
    result.assert_outcomes(passed=0, failed=4)


@pytest.mark.deprecated
def test_outlined_scenario_and_feature_with_extra_parameter_join(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Examples:
                | fruits    | extra      |
                | apples    | not used   |
                | oranges   | not needed |

                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | start | eat | left |
                    |   12  |  5  |  7   |
                    |    5  |  4  |  1   |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest(
        "-s",
        "-W ignore::pytest_bdd.PytestBDDScenarioExamplesExtraParamsWarning",
        "-W ignore::pytest_bdd.PytestBDDScenarioStepsExtraPramsWarning",
    )
    result.assert_outcomes(passed=4)


@pytest.mark.deprecated
def test_outlined_scenario_and_feature_with_combine_extra_and_insufficient_parameter_join(testdir):
    testdir.makefile(
        ".feature",
        outline="""\
            Feature: Outline
                Examples:
                | fruits    | extra      |
                | apples    | not used   |
                | oranges   | not needed |

                Examples:
                | fruits    |
                | cucumbers |
                | peaches   |

                Scenario Outline: Outlined given, when, thens
                    Given there are <start> <fruits>
                    When I eat <eat> <fruits>
                    Then I should have <left> <fruits>

                    Examples:
                    | start | eat | left |
                    |   12  |  5  |  7   |
                    |    5  |  4  |  1   |

                    Examples:
                    | eat | left |
                    |  8  |  6   |
                    |  9  |  5   |
            """,
    )

    testdir.makepyfile(STEPS_OUTLINED)
    result = testdir.runpytest(
        "-s",
        "-W ignore::pytest_bdd.PytestBDDScenarioExamplesExtraParamsWarning",
        "-W ignore::pytest_bdd.PytestBDDScenarioStepsExtraPramsWarning",
    )
    result.assert_outcomes(passed=8, failed=8)
