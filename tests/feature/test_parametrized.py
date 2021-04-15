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
