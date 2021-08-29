import textwrap


# TODO: This test was testing a behaviour that is different now. Do we want to support it?
#  I think not, but not sure
def test_parametrized(testdir):
    """Test parametrized scenario."""
    testdir.makefile(
        ".feature",
        parametrized=textwrap.dedent(
            """\
            Feature: Parametrized scenario
                Scenario: Parametrized given, when, thens
                    Given there are {start} cucumbers
                    When I eat {eat} cucumbers
                    Then I should have {left} cucumbers
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenario, parsers


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

        @given(parsers.parse("there are {start} cucumbers"), target_fixture="start_cucumbers")
        def start_cucumbers(start):
            return dict(start=start)


        @when(parsers.parse("I eat {eat} cucumbers"))
        def eat_cucumbers(start_cucumbers, start, eat):
            start_cucumbers["eat"] = eat


        @then(parsers.parse("I should have {left} cucumbers"))
        def should_have_left_cucumbers(start_cucumbers, start, eat, left):
            assert start - eat == left
            assert int(left) == start_cucumbers["start"] - start_cucumbers["eat"]

        """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=3)
    # TODO: We should test the parametrization of each test item, otherwise it's quite useless
