import textwrap

from pytest_bdd.utils import collect_dumped_objects


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
        from pytest_bdd import given, when, then, scenario, parsers
        from pytest_bdd.utils import dump_obj
        @pytest.fixture(params=[1, 2])
        def foo_bar(request):
            return "bar" * request.param
        @pytest.mark.parametrize(["start", "eat", "left"], [(12, 5, 7)])
        @scenario(
            "parametrized.feature", "Parametrized given, when, thens",
            examples_fixtures_mapping={'start', 'eat', 'left'}
        )
        def test_parametrized(request, start, eat, left):
            pass
        @pytest.mark.parametrize(["start", "eat", "left"], [(2, 1, 1)])
        @scenario(
            "parametrized.feature", "Parametrized given, when, thens",
            examples_fixtures_mapping={'start', 'eat', 'left'}
        )
        def test_parametrized_with_other_fixtures(request, start, eat, left, foo_bar):
            pass
        @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
        def start_cucumbers(start):
            dump_obj(start)
            return dict(start=start)
        @when(parsers.parse("I eat {eat:d} cucumbers"))
        def eat_cucumbers(start_cucumbers, start, eat):
            dump_obj(eat)
            start_cucumbers["eat"] = eat
        @then(parsers.parse("I should have {left:d} cucumbers"))
        def should_have_left_cucumbers(start_cucumbers, start, eat, left):
            dump_obj(left)
            assert start - eat == left
            assert start_cucumbers["start"] == start
            assert start_cucumbers["eat"] == eat
        """
        )
    )
    result = testdir.runpytest("-s", "-W", "ignore::pytest.PytestDeprecationWarning")
    result.assert_outcomes(passed=3)

    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, 5, 7,
        # The second test uses is duplicated because of the `foo_bar` indirect fixture
        2, 1, 1,
        2, 1, 1,
    ]
    # fmt: on


def test_parametrized_mapped_from_fixtures(testdir):
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
        from pytest_bdd import given, when, then, scenario, parsers
        from pytest_bdd.utils import dump_obj

        @pytest.mark.parametrize(["start_fixture", "eat_fixture", "left_fixture"], [(12, 5, 7)])
        @scenario(
            "parametrized.feature", "Parametrized given, when, thens",
            examples_fixtures_mapping={'start':'start_fixture', 'eat': 'eat_fixture', 'left':'left_fixture'}
        )
        def test_parametrized(request, start_fixture, eat_fixture, left_fixture):
            pass

        @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
        def start_cucumbers(start):
            dump_obj(start)
            return dict(start=start)
        @when(parsers.parse("I eat {eat:d} cucumbers"))
        def eat_cucumbers(start_cucumbers, start, eat):
            dump_obj(eat)
            start_cucumbers["eat"] = eat
        @then(parsers.parse("I should have {left:d} cucumbers"))
        def should_have_left_cucumbers(start_cucumbers, start, eat, left):
            dump_obj(left)
            assert start - eat == left
            assert start_cucumbers["start"] == start
            assert start_cucumbers["eat"] == eat
        """
        )
    )
    result = testdir.runpytest("-s", "-W", "ignore::pytest.PytestDeprecationWarning")
    result.assert_outcomes(passed=1)

    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, 5, 7,
    ]
    # fmt: on


def test_parametrized_mapped_from_fixtures_joining(testdir):
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
                Examples:
                    | start | eat | left |
                    |    13 |   6 |    7 |
                    |    12 |   5 |    7 |
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenario, parsers
        from pytest_bdd.utils import dump_obj

        @pytest.mark.parametrize(["start_fixture", "eat_fixture"], [(12, 5)])
        @scenario(
            "parametrized.feature", "Parametrized given, when, thens",
            examples_fixtures_mapping={'start':'start_fixture', 'eat': 'eat_fixture'}
        )
        def test_parametrized(request, start_fixture, eat_fixture):
            pass

        @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
        def start_cucumbers(start):
            dump_obj(start)
            return dict(start=start)
        @when(parsers.parse("I eat {eat:d} cucumbers"))
        def eat_cucumbers(start_cucumbers, start, eat):
            dump_obj(eat)
            start_cucumbers["eat"] = eat
        @then(parsers.parse("I should have {left:d} cucumbers"))
        def should_have_left_cucumbers(start_cucumbers, start, eat, left):
            dump_obj(left)
            assert start - eat == left
            assert start_cucumbers["start"] == start
            assert start_cucumbers["eat"] == eat
        """
        )
    )
    result = testdir.runpytest("-s", "-W", "ignore::pytest.PytestDeprecationWarning")
    result.assert_outcomes(passed=1, skipped=1)

    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, 5, 7,
    ]
    # fmt: on


def test_parametrized_mapped_from_fixtures_joining_no_affected_by_non_exisiting_keys(testdir):
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
                Examples:
                    | start | eat | left | param_external |
                    |    13 |   6 |    7 |         foo    |
                    |    12 |   5 |    7 |         bar    |
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then, scenario, parsers
        from pytest_bdd.utils import dump_obj

        @pytest.mark.parametrize(["start_fixture", "eat_fixture"], [(12, 5)])
        @scenario(
            "parametrized.feature", "Parametrized given, when, thens",
            examples_fixtures_mapping={'start':'start_fixture', 'eat': 'eat_fixture',
            'param_external': 'extra',
            }
        )
        def test_parametrized(request, start_fixture, eat_fixture):
            pass

        @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
        def start_cucumbers(start):
            dump_obj(start)
            return dict(start=start)
        @when(parsers.parse("I eat {eat:d} cucumbers"))
        def eat_cucumbers(start_cucumbers, start, eat):
            dump_obj(eat)
            start_cucumbers["eat"] = eat
        @then(parsers.parse("I should have {left:d} cucumbers"))
        def should_have_left_cucumbers(start_cucumbers, start, eat, left):
            dump_obj(left)
            assert start - eat == left
            assert start_cucumbers["start"] == start
            assert start_cucumbers["eat"] == eat
        """
        )
    )
    result = testdir.runpytest(
        "-s",
        "-W",
        "ignore::pytest.PytestDeprecationWarning",
        "-W",
        "ignore::pytest_bdd.PytestBDDScenarioExamplesExtraParamsWarning",
    )
    result.assert_outcomes(passed=1, skipped=1)

    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, 5, 7,
    ]
    # fmt: on


def test_parametrized_not_all_params(testdir):
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
        from pytest_bdd import given, when, then, scenario, parsers
        from pytest_bdd.utils import dump_obj

        @pytest.mark.parametrize(["start", "eat"], [(12, 5)])
        @scenario(
            "parametrized.feature", "Parametrized given, when, thens",
            examples_fixtures_mapping={'start', 'eat'}
        )
        def test_parametrized(request, start, eat):
            pass
        @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="start_cucumbers")
        def start_cucumbers(start):
            dump_obj(start)
            return dict(start=start)
        @when(parsers.parse("I eat {eat:d} cucumbers"))
        def eat_cucumbers(start_cucumbers, start, eat):
            dump_obj(eat)
            start_cucumbers["eat"] = eat

        @then(parsers.string("I should have <left> cucumbers"))
        def should_have_left_cucumbers(start_cucumbers, start, eat):
            assert start - eat == 7
            assert start_cucumbers["start"] == start
            assert start_cucumbers["eat"] == eat
        """
        )
    )
    result = testdir.runpytest(
        "-s",
        "-W",
        "ignore::pytest.PytestCollectionWarning",
        "-W",
        "ignore::pytest.PytestDeprecationWarning",
    )
    result.assert_outcomes(passed=1)

    parametrizations = collect_dumped_objects(result)
    # fmt: off
    assert parametrizations == [
        12, 5
    ]
    # fmt: on
