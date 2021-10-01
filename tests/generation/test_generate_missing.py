"""Code generation and assertion tests."""
import itertools
import textwrap

from pytest_bdd.scenario import get_python_name_generator
from tests.utils import assert_outcomes


def test_python_name_generator():
    """Test python name generator function."""
    assert list(itertools.islice(get_python_name_generator("Some name"), 3)) == [
        "test_some_name",
        "test_some_name_1",
        "test_some_name_2",
    ]


def test_generate_missing(testdir):
    """Test generate missing command."""
    testdir.makefile(
        ".feature",
        generation=textwrap.dedent(
            """\
            Feature: Missing code generation

                Background:
                    Given I have a foobar

                Scenario: Scenario tests which are already bound to the tests stay as is
                    Given I have a bar


                Scenario: Code is generated for scenarios which are not bound to any tests
                    Given I have a bar


                Scenario: Code is generated for scenario steps which are not yet defined(implemented)
                    Given I have a custom bar
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import functools

        from pytest_bdd import scenario, given

        scenario = functools.partial(scenario, "generation.feature")

        @given("I have a bar")
        def i_have_a_bar():
            return "bar"

        @scenario("Scenario tests which are already bound to the tests stay as is")
        def test_foo():
            pass

        @scenario("Code is generated for scenario steps which are not yet defined(implemented)")
        def test_missing_steps():
            pass
        """
        )
    )

    result = testdir.runpytest("--generate-missing", "--feature", "generation.feature")
    assert_outcomes(result, passed=0, failed=0, errors=0)
    assert not result.stderr.str()
    assert result.ret == 0

    result.stdout.fnmatch_lines(
        ['Scenario "Code is generated for scenarios which are not bound to any tests" is not bound to any test *']
    )

    result.stdout.fnmatch_lines(
        [
            'Step Given "I have a custom bar" is not defined in the scenario '
            '"Code is generated for scenario steps which are not yet defined(implemented)" *'
        ]
    )

    result.stdout.fnmatch_lines(
        ['Step Given "I have a foobar" is not defined in the background of the feature "Missing code generation" *']
    )

    result.stdout.fnmatch_lines(["Please place the code above to the test file(s):"])


def test_generate_missing_with_step_parsers(testdir):
    """Test that step parsers are correctly discovered and won't be part of the missing steps."""
    testdir.makefile(
        ".feature",
        generation=textwrap.dedent(
            """\
            Feature: Missing code generation with step parsers

                Scenario: Step parsers are correctly discovered
                    Given I use the string parser without parameter
                    And I use parsers.parse with parameter 1
                    And I use parsers.re with parameter 2
                    And I use parsers.cfparse with parameter 3
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import functools

        from pytest_bdd import scenarios, given, parsers

        scenarios("generation.feature")

        @given("I use the string parser without parameter")
        def i_have_a_bar():
            return None

        @given(parsers.parse("I use parsers.parse with parameter {param}"))
        def i_have_n_baz(param):
            return param

        @given(parsers.re(r"^I use parsers.re with parameter (?P<param>.*?)$"))
        def i_have_n_baz(param):
            return param

        @given(parsers.cfparse("I use parsers.cfparse with parameter {param:d}"))
        def i_have_n_baz(param):
            return param
        """
        )
    )

    result = testdir.runpytest("--generate-missing", "--feature", "generation.feature")
    assert_outcomes(result, passed=0, failed=0, errors=0)
    assert not result.stderr.str()
    assert result.ret == 0

    output = result.stdout.str()

    assert "I use the string parser" not in output
    assert "I use parsers.parse" not in output
    assert "I use parsers.re" not in output
    assert "I use parsers.cfparse" not in output
