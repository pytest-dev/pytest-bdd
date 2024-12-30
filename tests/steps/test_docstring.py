from __future__ import annotations

import textwrap

from src.pytest_bdd.utils import collect_dumped_objects


def test_steps_with_docstrings(pytester):
    pytester.makefile(
        ".feature",
        docstring=textwrap.dedent(
            '''
            Feature: Docstring

              Scenario: Step with plain docstring as multiline step
                Given a step has a docstring
                """
                This is a given docstring
                """

                When a step provides a docstring with lower indentation
                """
            This is a when docstring
                """

                And this step has no docstring

                Then this step has a greater indentation
                """
                        This is a then docstring
                """
            '''
        ),
    )

    pytester.makeconftest(
        textwrap.dedent(
            r"""
        from pytest_bdd import given, when, then
        from pytest_bdd.utils import dump_obj


        @given("a step has a docstring")
        def _(docstring):
            given_docstring = docstring
            dump_obj(given_docstring)


        @when("a step provides a docstring with lower indentation")
        def _(docstring):
            when_docstring = docstring
            dump_obj(when_docstring)


        @when("this step has no docstring")
        def _():
            pass


        @then("this step has a greater indentation")
        def _(docstring):
            then_docstring = docstring
            dump_obj(then_docstring)
            """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import scenarios

            scenarios("docstring.feature")
            """
        )
    )

    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)

    docstrings = collect_dumped_objects(result)
    assert docstrings == ["This is a given docstring", "This is a when docstring", "This is a then docstring"]


def test_steps_with_missing_docstring(pytester):
    pytester.makefile(
        ".feature",
        missing_docstring=textwrap.dedent(
            '''\
            Feature: Missing docstring

              Scenario: Docstring is missing for a step
                Given this step has a docstring
                """
                This is a given docstring
                """

                When this step has no docstring but tries to use the docstring argument
                Then an error is thrown
            '''
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then


        @given("this step has a docstring")
        def _(docstring):
            print(docstring)


        @when("this step has no docstring but tries to use the docstring argument")
        def _(docstring):
            print(docstring)


        @then("an error is thrown")
        def _():
            pass

    """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenarios

        scenarios("missing_docstring.feature")
        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*fixture 'docstring' not found*"])


def test_docstring_argument_in_step_impl_is_optional(pytester):
    pytester.makefile(
        ".feature",
        optional_docstring_arg=textwrap.dedent(
            '''\
            Feature: Missing docstring

              Scenario: Docstring arg is missing for a step definition
                Given this step has a docstring
                """
                This is a given docstring
                """

                When this step has a docstring but no docstring argument
                """
                This is a when docstring
                """

                Then the test passes
            '''
        ),
    )
    pytester.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then


        @given("this step has a docstring")
        def _(docstring):
            print(docstring)


        @when("this step has a docstring but no docstring argument")
        def _():
            pass


        @then("the test passes")
        def _():
            pass

    """
        )
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenarios

        scenarios("optional_docstring_arg.feature")
        """
        )
    )
    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=1)


def test_docstring_step_argument_is_reserved_and_cannot_be_used(pytester):
    pytester.makefile(
        ".feature",
        reserved_docstring_arg=textwrap.dedent(
            """\
            Feature: Reserved docstring argument

              Scenario: Reserved docstring argument
                Given this step has a {docstring} argument
                Then the test fails
            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario, given, then, parsers

        @scenario("reserved_docstring_arg.feature", "Reserved docstring argument")
        def test_docstring():
            pass


        @given(parsers.parse("this step has a {docstring} argument"))
        def _(docstring):
            pass


        @then("the test fails")
        def _():
            pass
        """
        )
    )

    result = pytester.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(
        [
            "*Step 'this step has a {docstring} argument' defines argument names that are reserved: 'docstring'. Please use different names.*"
        ]
    )
