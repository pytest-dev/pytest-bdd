"""Tests for the ``bdd_setup_step_fixtures`` ini option."""

from __future__ import annotations

import textwrap

import pytest

FEATURE = textwrap.dedent(
    """\
    Feature: Step fixtures
        Scenario: Step uses a fixture
            Given a step with a fixture
    """
)


def enable_option(pytester):
    pytester.makeini(
        """
        [pytest]
        bdd_setup_step_fixtures = true
        """
    )


@pytest.mark.parametrize("enabled, outcome", [(False, {"failed": 1}), (True, {"errors": 1})])
def test_failing_step_fixture(pytester, enabled, outcome):
    if enabled:
        enable_option(pytester)
    pytester.makefile(".feature", steps=FEATURE)
    pytester.makepyfile(
        textwrap.dedent(
            """\
            import pytest
            from pytest_bdd import given, scenarios

            scenarios("steps.feature")


            @pytest.fixture(scope="module")
            def broken():
                assert False, "broken setup"


            @given("a step with a fixture")
            def _(broken):
                pass
            """
        )
    )

    result = pytester.runpytest()

    result.assert_outcomes(**outcome)
    result.stdout.fnmatch_lines(["*broken setup*"])


def test_step_fixtures_are_created_once(pytester):
    enable_option(pytester)
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Step fixtures
                Scenario: Two steps share a fixture
                    Given a step with a fixture
                    Then the fixture was created once
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
            import pytest
            from pytest_bdd import given, then, scenarios

            scenarios("steps.feature")

            created = []


            @pytest.fixture
            def resource():
                created.append(1)
                return "resource"


            @given("a step with a fixture")
            def _(resource):
                assert resource == "resource"


            @then("the fixture was created once")
            def _(resource):
                assert created == [1]
            """
        )
    )

    pytester.runpytest().assert_outcomes(passed=1)


def test_fixtures_depending_on_target_fixture_are_left_to_the_steps(pytester):
    enable_option(pytester)
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Step fixtures
                Scenario: Fixture depends on a target fixture
                    Given there is an article
                    Then the article title is "Hello"
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
            import pytest
            from pytest_bdd import given, then, parsers, scenarios

            scenarios("steps.feature")


            @pytest.fixture
            def article():
                raise RuntimeError("should be overridden by the given step")


            @pytest.fixture
            def title(article):
                return article["title"]


            @given("there is an article", target_fixture="article")
            def _():
                return {"title": "Hello"}


            @then(parsers.parse('the article title is "{expected}"'))
            def _(title, expected):
                assert title == expected
            """
        )
    )

    pytester.runpytest().assert_outcomes(passed=1)


def test_overriding_fixture_that_depends_on_target_fixture(pytester):
    enable_option(pytester)
    pytester.makeconftest(
        textwrap.dedent(
            """\
            import pytest


            @pytest.fixture
            def article():
                raise RuntimeError("should be overridden by the given step")


            @pytest.fixture
            def title(article):
                return article["title"]
            """
        )
    )
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Step fixtures
                Scenario: Overridden fixture depends on a target fixture
                    Given there is an article
                    Then the title is "HELLO"
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
            import pytest
            from pytest_bdd import given, then, parsers, scenarios

            scenarios("steps.feature")


            @pytest.fixture
            def title(title):
                return title.upper()


            @given("there is an article", target_fixture="article")
            def _():
                return {"title": "Hello"}


            @then(parsers.parse('the title is "{expected}"'))
            def _(title, expected):
                assert title == expected
            """
        )
    )

    pytester.runpytest().assert_outcomes(passed=1)


def test_scenario_outline(pytester):
    enable_option(pytester)
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            """\
            Feature: Step fixtures
                Scenario Outline: Outline uses a fixture
                    Given the fixture is <state>

                    Examples:
                        | state  |
                        | ok     |
                        | broken |
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
            import pytest
            from pytest_bdd import given, parsers, scenarios

            scenarios("steps.feature")


            @pytest.fixture
            def resource(request):
                return "resource"


            @pytest.fixture
            def broken_resource():
                assert False, "broken setup"


            @given("the fixture is ok")
            def _(resource):
                pass


            @given("the fixture is broken")
            def _(broken_resource):
                pass
            """
        )
    )

    pytester.runpytest().assert_outcomes(passed=1, errors=1)


def test_step_arguments_datatable_and_docstring_are_not_requested_as_fixtures(pytester):
    enable_option(pytester)
    pytester.makefile(
        ".feature",
        steps=textwrap.dedent(
            '''\
            Feature: Step fixtures
                Scenario: Step arguments
                    Given the number 3
                    And a table
                        | a |
                    And a text
                        """
                        hello
                        """
            '''
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import given, parsers, scenarios

            scenarios("steps.feature")


            @given(parsers.parse("the number {number:d}"))
            def _(number):
                assert number == 3


            @given("a table")
            def _(datatable):
                assert datatable == [["a"]]


            @given("a text")
            def _(docstring):
                assert docstring == "hello"
            """
        )
    )

    pytester.runpytest().assert_outcomes(passed=1)


def test_regular_tests_are_not_affected(pytester):
    enable_option(pytester)
    pytester.makepyfile(
        textwrap.dedent(
            """\
            def test_plain(tmp_path):
                assert tmp_path.exists()
            """
        )
    )

    pytester.runpytest().assert_outcomes(passed=1)


def test_missing_step_definition_is_still_reported_by_the_scenario(pytester):
    enable_option(pytester)
    pytester.makefile(".feature", steps=FEATURE)
    pytester.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import scenarios

            scenarios("steps.feature")
            """
        )
    )

    result = pytester.runpytest()

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*Step definition is not found*"])
