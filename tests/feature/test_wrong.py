"""Test wrong feature syntax."""

import textwrap
import pytest

from pytest_bdd import scenario, scenarios
from pytest_bdd import exceptions


def test_when_in_background(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: When in background

                Background:
                    Given I don't always write when in the background, but
                    When I do

                Scenario: When in background
                    Then its fine
                    When I do it again
                    Then its wrong
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import scenario

        @scenario("wrong.feature", "When in background")
        def test_wrong():
            pass

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 2
    result.stdout.fnmatch_lines("*FeatureError: Background section can only contain Given steps.*")


def test_then_first(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: Then first
                Scenario: Then first
                    Then it won't work

            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import scenario

        @scenario("wrong.feature", "Then first")
        def test_wrong():
            pass

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 2
    result.stdout.fnmatch_lines("*FeatureError: Then steps must follow Given or When steps.*")


def test_given_after_when(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: Given after when
                Scenario: Given after When
                    Given something
                    When something else
                    Given won't work
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import scenario

        @scenario("wrong.feature", "Given after When")
        def test_wrong():
            pass

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 2
    result.stdout.fnmatch_lines("*FeatureError: Given steps must be the first within the Scenario.*")


def test_given_after_then(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: Given after then
                Scenario: Given after Then
                    Given something
                    When something else
                    Then nevermind
                    Given won't work
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import scenario

        @scenario("wrong.feature", "Given after Then")
        def test_wrong():
            pass

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 2
    result.stdout.fnmatch_lines("*FeatureError: Given steps must be the first within the Scenario.*")


def test_when_in_given(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: When in given
                Scenario: When in Given
                    Given something else
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import when, scenario

        @scenario("wrong.feature", "When in Given")
        def test_wrong():
            pass

        @when("something else")
        def something_else():
            pass

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(
        "*StepDefinitionNotFoundError: "
        'Step definition is not found: Given "something else". Line 3 in scenario "When in Given"*'
    )


def test_when_in_then(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: When in then
                Scenario: When in Then
                    When something else
                    Then something else
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import when, scenario

        @scenario("wrong.feature", "When in Then")
        def test_wrong():
            pass

        @when("something else")
        def something_else():
            pass

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(
        "*StepDefinitionNotFoundError: "
        'Step definition is not found: Then "something else". Line 4 in scenario "When in Then"*'
    )


def test_then_in_given(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: Then in given
                Scenario: Then in Given
                    Given nevermind
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import then, scenario

        @scenario("wrong.feature", "Then in Given")
        def test_wrong():
            pass

        @then("nevermind")
        def nevermind():
            assert True
        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(
        "*StepDefinitionNotFoundError: "
        'Step definition is not found: Given "nevermind". Line 3 in scenario "Then in Given"*'
    )


def test_given_in_when(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: Given in when
                Scenario: Given in When
                    When something
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, scenario

        @scenario("wrong.feature", "Given in When")
        def test_wrong():
            pass

        @given("something")
        def something():
            return "something"

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(
        "*StepDefinitionNotFoundError: "
        'Step definition is not found: When "something". Line 3 in scenario "Given in When"*'
    )


def test_given_in_then(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: Given in then
                Scenario: Given in Then
                    When something else
                    Then something
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, scenario

        @scenario("wrong.feature", "Given in Then")
        def test_wrong():
            pass


        @when("something else")
        def something_else():
            pass


        @given("something")
        def something():
            return "something"

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(
        "*StepDefinitionNotFoundError: "
        'Step definition is not found: Then "something". Line 4 in scenario "Given in Then"*'
    )


def test_then_in_when(testdir):
    testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: Then in when
                Scenario: Then in When
                    When nevermind
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import then, scenario

        @scenario("wrong.feature", "Then in When")
        def test_wrong():
            pass

        @then("nevermind")
        def nevermind():
            assert True
        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 1
    result.stdout.fnmatch_lines(
        "*StepDefinitionNotFoundError: "
        'Step definition is not found: When "nevermind". Line 3 in scenario "Then in When"*'
    )


def test_verbose_output(testdir):
    """Test verbose output of failed feature scenario."""
    feature = testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: When in background

                Background:
                    Given I don't always write when in the background, but
                    When I do

                Scenario: When in background
                    Then its fine
                    When I do it again
                    Then its wrong
        """
        ),
    )

    with pytest.raises(exceptions.FeatureError) as excinfo:
        scenario(feature.strpath, "When in background")

    msg, line_number, line, file = excinfo.value.args

    assert line_number == 5
    assert line == "When I do"
    assert file == feature.strpath
    assert line in str(excinfo.value)


def test_multiple_features_single_file(testdir):
    """Test validation error when multiple features are placed in a single file."""
    feature = testdir.makefile(
        ".feature",
        wrong=textwrap.dedent(
            """\
            Feature: Feature One

              Background:
                Given I have A
                And I have B

              Scenario: Do something with A
                When I do something with A
                Then something about B

            Feature: Feature Two

              Background:
                Given I have A

              Scenario: Something that just needs A
                When I do something else with A
                Then something else about B

              Scenario: Something that needs B again
                Given I have B
                When I do something else with B
                Then something else about A and B
        """
        ),
    )

    with pytest.raises(exceptions.FeatureError) as excinfo:
        scenarios(feature.strpath)
    assert excinfo.value.args[0] == "Multiple features are not allowed in a single feature file"
