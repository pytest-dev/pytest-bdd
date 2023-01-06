from pathlib import Path
from textwrap import dedent


def test_autoload_disabled_with_conftest_on_same_level(testdir):
    testdir.makefile(
        ".feature",
        # language=gherkin
        steps="""\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: Executed step by step
                    Given I have a foo fixture with value "foo"
                    And there is a list
                    When I append 1 to the list
                    And I append 2 to the list
                    And I append 3 to the list
                    Then foo should have value "foo"
                    But the list should be [1, 2, 3]

                Examples:
                    | run |
                    |  1  |
                    |  2  |
            """,
    )

    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import given, when, then, scenario

        @scenario('steps.feature')
        def test():
            ...

        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def foo():
            return "foo"

        @given("there is a list", target_fixture="results")
        def results():
            return []

        @when("I append 1 to the list")
        def append_1(results):
            results.append(1)

        @when("I append 2 to the list")
        def append_2(results):
            results.append(2)

        @when("I append 3 to the list")
        def append_3(results):
            results.append(3)

        @then('foo should have value "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"

        @then("the list should be [1, 2, 3]")
        def check_results(results):
            assert results == [1, 2, 3]
        """
    )
    result = testdir.runpytest("--disable-feature-autoload")
    result.assert_outcomes(passed=2, failed=0)


def test_autoload_disabled_with_conftest_on_higher_level(testdir):
    testdir.makepyfile(
        # language=python
        """\
        from pytest_bdd import given, when, then, scenario

        @scenario('steps.feature', features_base_dir='features')
        def test():
            ...

        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def foo():
            return "foo"

        @given("there is a list", target_fixture="results")
        def results():
            return []

        @when("I append 1 to the list")
        def append_1(results):
            results.append(1)

        @when("I append 2 to the list")
        def append_2(results):
            results.append(2)

        @when("I append 3 to the list")
        def append_3(results):
            results.append(3)

        @then('foo should have value "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"

        @then("the list should be [1, 2, 3]")
        def check_results(results):
            assert results == [1, 2, 3]
        """
    )

    Path(testdir.mkdir("features") / "steps.feature").write_text(
        dedent(
            # language=gherkin
            """\
            Feature: Steps are executed one by one
                Steps are executed one by one. Given and When sections
                are not mandatory in some cases.

                Scenario: Executed step by step
                    Given I have a foo fixture with value "foo"
                    And there is a list
                    When I append 1 to the list
                    And I append 2 to the list
                    And I append 3 to the list
                    Then foo should have value "foo"
                    But the list should be [1, 2, 3]

                Examples:
                    | run |
                    |  1  |
                    |  2  |
            """
        ),
    )

    result = testdir.runpytest("--disable-feature-autoload")
    result.assert_outcomes(passed=2, failed=0)
