"""Scenario Outline tests."""
import textwrap

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


def test_outlined(testdir):
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


def test_disallow_free_example_params(testdir):
    """Test parametrized scenario when the test function lacks parameters."""

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with wrong examples
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left | unknown_param |
                    |  12   |  5  |  7   | value         |

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
            "Outlined with wrong examples",
            allow_example_free_variables=False
        )
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        '*ScenarioExamplesNotValidError: Scenario "Outlined with wrong examples"*does not have valid examples*'
    )
    result.stdout.fnmatch_lines(
        "*Set of example parameters [[]'eat', 'left', 'start', 'unknown_param'[]] should be "
        "a subset of step parameters [[]'eat', 'left', 'start'[]]*"
    )


def test_disallow_free_example_params_by_ini(testdir):
    """Test parametrized scenario when the test function lacks parameters."""
    testdir.makeini(
        """
            [pytest]
            bdd_allow_example_free_variables=false
        """
    )

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with wrong examples
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left | unknown_param |
                    |  12   |  5  |  7   | value         |

            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with wrong examples")
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        '*ScenarioExamplesNotValidError: Scenario "Outlined with wrong examples"*does not have valid examples*'
    )
    result.stdout.fnmatch_lines(
        "*Set of example parameters [[]'eat', 'left', 'start', 'unknown_param'[]] should be "
        "a subset of step parameters [[]'eat', 'left', 'start'[]]*"
    )


def test_allow_free_example_params(testdir):
    """Test parametrized scenario when the test function has a subset of the parameters of the examples."""

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with subset of examples
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left | notes             |
                    |  12   |  5  |  7   | Should be ignored |

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
            "Outlined with subset of examples",
            allow_example_free_variables=True
        )
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, passed=1)


def test_allow_free_example_params_by_ini(testdir):
    """Test parametrized scenario when the test function has a subset of the parameters of the examples."""

    testdir.makeini(
        """
            [pytest]
            bdd_allow_example_free_variables=true
        """
    )

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with subset of examples
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                    | start | eat | left | notes             |
                    |  12   |  5  |  7   | Should be ignored |

            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("outline.feature", "Outlined with subset of examples")
        def test_outline(request):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, passed=1)


def test_disallow_outlined_parameters_not_a_subset_of_examples(testdir):
    """Test parametrized scenario when the test function has a parameter set
    which is not a subset of those in the examples table."""

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with wrong examples
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers in my <right> bucket

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   |

            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario, then
        import pytest_bdd.parsers as parsers

        @scenario("outline.feature", "Outlined with wrong examples", allow_step_free_variables=False)
        def test_outline(request):
            pass

        @then(parsers.parse('I should have {left} cucumbers in my <right> bucket'))
        def stepdef(left):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        '*ScenarioExamplesNotValidError: Scenario "Outlined with wrong examples"*does not have valid examples*',
    )
    result.stdout.fnmatch_lines("*should be a subset of example parameters [[]'eat', 'left', 'start'[]]*")


def test_disallow_outlined_parameters_not_a_subset_of_examples_by_ini(testdir):
    """Test parametrized scenario when the test function has a parameter set
    which is not a subset of those in the examples table."""
    testdir.makeini(
        """
            [pytest]
            bdd_allow_step_free_variables=false
        """
    )

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with wrong examples
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers in my <right> bucket

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   |

            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario, then
        import pytest_bdd.parsers as parsers

        @scenario("outline.feature", "Outlined with wrong examples")
        def test_outline(request):
            pass

        @then(parsers.parse('I should have {left} cucumbers in my <right> bucket'))
        def stepdef(left):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(
        '*ScenarioExamplesNotValidError: Scenario "Outlined with wrong examples"*does not have valid examples*',
    )
    result.stdout.fnmatch_lines("*should be a subset of example parameters [[]'eat', 'left', 'start'[]]*")


def test_allow_outlined_parameters_not_a_subset_of_examples(testdir):
    """Test parametrized scenario when the test function has a parameter set
    which is not a subset of those in the examples table."""

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with wrong examples
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers in my <right> bucket

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   |

            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario, then
        import pytest_bdd.parsers as parsers

        @scenario("outline.feature", "Outlined with wrong examples", allow_step_free_variables=True)
        def test_outline(request):
            pass

        @then(parsers.parse('I should have {left} cucumbers in my <right> bucket'))
        def stepdef(left):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, passed=1)


def test_allow_outlined_parameters_not_a_subset_of_examples_by_ini(testdir):
    """Test parametrized scenario when the test function has a parameter set
    which is not a subset of those in the examples table."""

    testdir.makeini(
        """
            [pytest]
            bdd_allow_step_free_variables=true
        """
    )

    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with wrong examples
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers in my <right> bucket

                    Examples:
                    | start | eat | left |
                    |  12   |  5  |  7   |

            """
        ),
    )
    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario, then
        import pytest_bdd.parsers as parsers

        @scenario("outline.feature", "Outlined with wrong examples")
        def test_outline(request):
            pass

        @then(parsers.parse('I should have {left} cucumbers in my <right> bucket'))
        def stepdef(left):
            pass
        """
        )
    )
    result = testdir.runpytest()
    assert_outcomes(result, passed=1)


def test_wrong_vertical_examples_scenario(testdir):
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

                    Examples: Vertical
                    | start | 12 | 2 |
                    | start | 10 | 1 |
                    | left  | 7  | 1 |
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


def test_wrong_vertical_examples_feature(testdir):
    """Test parametrized feature vertical example table has wrong format."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outlines

                Examples: Vertical
                | start | 12 | 2 |
                | start | 10 | 1 |
                | left  | 7  | 1 |

                Scenario Outline: Outlined with wrong vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers
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


def test_vertical_example(testdir):
    """Test outlined scenario with vertical examples table."""
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outline
                Scenario Outline: Outlined with vertical example table
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples: Vertical
                    | start | 12 | 2 |
                    | eat   | 5  | 1 |
                    | left  | 7  | 1 |

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
            "Outlined with vertical example table",
        )
        def test_outline():
            pass
        """
        )
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


def test_outlined_feature(testdir):
    testdir.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
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
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, scenario, parsers
        from pytest_bdd.utils import dump_obj

        @scenario(
            "outline.feature",
            "Outlined given, when, thens",
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
        )
    )
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
