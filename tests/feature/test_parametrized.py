import textwrap


def test_parametrized(testdir):
    """Test parametrized scenario."""
    testdir.makefile(
        ".feature",
        parametrized=textwrap.dedent(
            """\
            Feature: Parametrized scenario
                Scenario: Parametrized given, when, thens
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenario


        @pytest.mark.parametrize(["start", "eat", "left"], [(12, 5, 7)])
        @scenario("parametrized.feature", "Parametrized given, when, thens")
        def test_parametrized(request, start, eat, left):
            pass

        @pytest.fixture(params=[1, 2])
        def foo_bar(request):
            return "bar" * request.param


        @pytest.mark.parametrize(["start", "eat", "left"], [(12, 5, 7)])
        @scenario("parametrized.feature", "Parametrized given, when, thens")
        def test_parametrized_with_other_fixtures(request, start, eat, left, foo_bar):
            pass

        @given("there are <start> cucumbers", target_fixture="start_cucumbers")
        def start_cucumbers(start):
            return dict(start=start)


        @when("I eat <eat> cucumbers")
        def eat_cucumbers(start_cucumbers, start, eat):
            start_cucumbers["eat"] = eat


        @then("I should have <left> cucumbers")
        def should_have_left_cucumbers(start_cucumbers, start, eat, left):
            assert start - eat == left
            assert start_cucumbers["start"] == start
            assert start_cucumbers["eat"] == eat

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=3)


def test_parametrized_with_parsers(testdir):
    """Test parametrized scenario."""
    testdir.makefile(
        ".feature",
        parametrized=textwrap.dedent(
            """\
            Feature: Parametrized scenario
                Scenario: Parametrized given, when, thens with parsers invocation
                    Given there are <start> gherkins
                    When I eat <eat> gherkins
                    Then I should have <left> gherkins
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenario
        from pytest_bdd.parsers import re, parse 

        @pytest.mark.parametrize(["start", "eat", "left"], [(12, 5, 7)])
        @scenario("parametrized.feature", "Parametrized given, when, thens with parsers invocation")
        def test_parametrized(request, start, eat, left):
            pass

        
        @given(re("there are <start> (?P<vegetables>\\\\w+)"), target_fixture="start_vegetables")
        def start_vegetables(start, vegetables):
            return dict(start=start)


        @when("I eat <eat> gherkins")
        def eat_cucumbers(start_vegetables, start, eat):
            start_vegetables["eat"] = eat


        @then(re("I should have (?P<left>\\\\d+) (?P<vegetables>\\\\w+)"), converters=dict(left=int))
        def should_have_left_vegetables(start_vegetables, start, eat, left, vegetables):
            assert start - eat == left
            assert start_vegetables["start"] == start
            assert start_vegetables["eat"] == eat

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
