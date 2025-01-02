"""Test scenario decorator."""

from __future__ import annotations

import textwrap

from pytest_bdd.utils import collect_dumped_objects


def test_scenario_not_found(pytester, pytest_params):
    """Test the situation when scenario is not found."""
    pytester.makefile(
        ".feature",
        not_found=textwrap.dedent(
            """\
            Feature: Scenario is not found

            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import re
        import pytest
        from pytest_bdd import parsers, given, then, scenario

        @scenario("not_found.feature", "NOT FOUND")
        def test_not_found():
            pass

        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)

    result.assert_outcomes(errors=1)
    result.stdout.fnmatch_lines('*Scenario "NOT FOUND" in feature "Scenario is not found" in*')


def test_scenario_comments(pytester):
    """Test comments inside scenario."""
    pytester.makefile(
        ".feature",
        comments=textwrap.dedent(
            """\
            Feature: Comments
                Scenario: Comments
                    # Comment
                    Given I have a bar

                Scenario: Strings that are not #comments
                    Given comments should be at the start of words
                    Then this is not a#comment
                    And this is not a # comment
                    And this is not "#acomment"

            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        import re
        import pytest
        from pytest_bdd import parsers, given, then, scenario

        @scenario("comments.feature", "Comments")
        def test_1():
            pass

        @scenario("comments.feature", "Strings that are not #comments")
        def test_2():
            pass


        @given("I have a bar")
        def _():
            return "bar"


        @given("comments should be at the start of words")
        def _():
            pass


        @then("this is not a#comment")
        @then("this is not a # comment")
        @then('this is not "#acomment"')
        def _():
            pass

        """
        )
    )

    result = pytester.runpytest()

    result.assert_outcomes(passed=2)


def test_scenario_not_decorator(pytester, pytest_params):
    """Test scenario function is used not as decorator."""
    pytester.makefile(
        ".feature",
        foo="""
        Feature: Test function is not a decorator
            Scenario: Foo
                Given I have a bar
        """,
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenario

        test_foo = scenario('foo.feature', 'Foo')
        """
    )

    result = pytester.runpytest_subprocess(*pytest_params)

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines("*ScenarioIsDecoratorOnly: scenario function can only be used as a decorator*")


def test_simple(pytester, pytest_params):
    """Test scenario decorator with a standard usage."""
    pytester.makefile(
        ".feature",
        simple="""
        Feature: Simple feature
            Scenario: Simple scenario
                Given I have a bar
        """,
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenario, given, then

        @scenario("simple.feature", "Simple scenario")
        def test_simple():
            pass

        @given("I have a bar")
        def _():
            return "bar"

        @then("pass")
        def _():
            pass
        """
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_angular_brackets_are_not_parsed(pytester):
    """Test that angular brackets are not parsed for "Scenario"s.

    (They should be parsed only when used in "Scenario Outline")

    """
    pytester.makefile(
        ".feature",
        simple="""
        Feature: Simple feature
            Scenario: Simple scenario
                Given I have a <tag>
                Then pass

            Scenario Outline: Outlined scenario
                Given I have a templated <foo>
                Then pass

            Examples:
                | foo |
                | bar |
        """,
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios, given, then, parsers

        scenarios("simple.feature")

        @given("I have a <tag>")
        def _():
            return "tag"

        @given(parsers.parse("I have a templated {foo}"))
        def _(foo):
            return "foo"

        @then("pass")
        def _():
            pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=2)


def test_example_params(pytester):
    """Test example params are rendered where necessary:
    * Step names
    * Docstring
    * Datatables
    """
    pytester.makefile(
        ".feature",
        example_params='''
        Feature: Example params
            Background:
                Given I have a background <background>
                And my background has:
                """
                Background <background>
                """

                Scenario Outline: Outlined scenario
                    Given I have a templated <foo>
                    When I have a templated datatable
                        | <data>  |
                        | example |
                    And I have a templated docstring
                    """
                    This is a <doc>
                    """
                    Then pass

                Examples:
                    | background | foo | data  | doc    |
                    | parameter  | bar | table | string |
        ''',
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios, given, when, then, parsers
        from pytest_bdd.utils import dump_obj

        scenarios("example_params.feature")


        @given(parsers.parse("I have a background {background}"))
        def _(background):
            return dump_obj(("background", background))


        @given(parsers.parse("I have a templated {foo}"))
        def _(foo):
            return "foo"


        @given("my background has:")
        def _(docstring):
            return dump_obj(("background_docstring", docstring))


        @given("I have a rule table:")
        def _(datatable):
            return dump_obj(("rule", datatable))


        @when("I have a templated datatable")
        def _(datatable):
            return dump_obj(("datatable", datatable))


        @when("I have a templated docstring")
        def _(docstring):
            return dump_obj(("docstring", docstring))


        @then("pass")
        def _():
            pass
        """
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)

    assert collect_dumped_objects(result) == [
        ("background", "parameter"),
        ("background_docstring", "Background parameter"),
        ("datatable", [["table"], ["example"]]),
        ("docstring", "This is a string"),
    ]


def test_step_parser_argument_not_in_function_signature_does_not_fail(pytester):
    """Test that if the step parser defines an argument, but step function does not accept it,
    then it does not fail and the params is just not filled."""

    pytester.makefile(
        ".feature",
        simple="""
        Feature: Simple feature
            Scenario: Step with missing argument
                Given a user with username "user1"
        """,
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios, given, parsers

        scenarios("simple.feature")

        @given(parsers.parse('a user with username "{username}"'))
        def create_user():
            pass
        """
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_multilanguage_support(pytester):
    """Test multilanguage support."""
    pytester.makefile(
        ".feature",
        simple="""
            # language: it

            Funzionalità: Funzionalità semplice

                Contesto:
                    Dato che uso uno step nel contesto
                    Allora va tutto bene

                Scenario: Scenario semplice
                    Dato che uso uno step con "Dato"
                    E che uso uno step con "E"
                    Ma che uso uno step con "Ma"
                    * che uso uno step con "*"
                    Allora va tutto bene

                Schema dello scenario: Scenario con schema
                    Dato che uso uno step con "<nome esempio>"
                    Allora va tutto bene

                    Esempi:
                    | nome esempio  |
                    | esempio 1     |
                    | esempio 2     |
        """,
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenario, given, then, parsers
        from pytest_bdd.utils import dump_obj

        @scenario("simple.feature", "Scenario semplice")
        def test_scenario_semplice():
            pass

        @scenario("simple.feature", "Scenario con schema")
        def test_scenario_con_schema():
            pass

        @given("che uso uno step nel contesto")
        def _():
            return dump_obj(("given", "che uso uno step nel contesto"))

        @given(parsers.parse('che uso uno step con "{step_name}"'))
        def _(step_name):
            return dump_obj(("given", "che uso uno step con ", step_name))

        @then("va tutto bene")
        def _():
            dump_obj(("then", "va tutto bene"))
        """
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=3)

    assert collect_dumped_objects(result) == [
        # 1st scenario
        ("given", "che uso uno step nel contesto"),
        ("then", "va tutto bene"),
        ("given", "che uso uno step con ", "Dato"),
        ("given", "che uso uno step con ", "E"),
        ("given", "che uso uno step con ", "Ma"),
        ("given", "che uso uno step con ", "*"),
        ("then", "va tutto bene"),
        # 2nd scenario
        # 1st example
        ("given", "che uso uno step nel contesto"),
        ("then", "va tutto bene"),
        ("given", "che uso uno step con ", "esempio 1"),
        ("then", "va tutto bene"),
        # 2nd example
        ("given", "che uso uno step nel contesto"),
        ("then", "va tutto bene"),
        ("given", "che uso uno step con ", "esempio 2"),
        ("then", "va tutto bene"),
    ]


def test_default_value_is_used_as_fallback(pytester):
    """Test that the default value for a step implementation is only used as a fallback."""
    pytester.makefile(
        ".feature",
        simple="""
        Feature: Simple feature
            Scenario: Step using default arg
                Given a user with default username

            Scenario: Step using explicit value
                Given a user with username "user1"
        """,
    )
    pytester.makepyfile(
        """
        from pytest_bdd import scenarios, given, then, parsers
        from pytest_bdd.utils import dump_obj

        scenarios("simple.feature")

        @given('a user with default username', target_fixture="user")
        @given(parsers.parse('a user with username "{username}"'), target_fixture="user")
        def create_user(username="defaultuser"):
            dump_obj(username)

        """
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=2)

    assert collect_dumped_objects(result) == ["defaultuser", "user1"]
