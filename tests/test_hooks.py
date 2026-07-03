from __future__ import annotations

import textwrap

from pytest_bdd.utils import collect_dumped_objects


def test_conftest_module_evaluated_twice(pytester):
    """Regression test for https://github.com/pytest-dev/pytest-bdd/issues/62"""
    pytester.makeconftest("")

    subdir = pytester.mkpydir("subdir")
    subdir.joinpath("conftest.py").write_text(
        textwrap.dedent(
            r"""
        def pytest_pyfunc_call(pyfuncitem):
            print('\npytest_pyfunc_call hook')

        def pytest_generate_tests(metafunc):
            print('\npytest_generate_tests hook')
    """
        )
    )

    subdir.joinpath("test_foo.py").write_text(
        textwrap.dedent(
            r"""
        from pytest_bdd import scenario

        @scenario('foo.feature', 'Some scenario')
        def test_foo():
            pass
    """
        )
    )

    subdir.joinpath("foo.feature").write_text(
        textwrap.dedent(
            r"""
        Feature: The feature
            Scenario: Some scenario
    """
        )
    )

    result = pytester.runpytest("-s")

    assert result.stdout.lines.count("pytest_pyfunc_call hook") == 1
    assert result.stdout.lines.count("pytest_generate_tests hook") == 1


def test_item_collection_does_not_break_on_non_function_items(pytester):
    """Regression test for https://github.com/pytest-dev/pytest-bdd/issues/317"""
    pytester.makeconftest(
        """
    import pytest

    @pytest.mark.tryfirst
    def pytest_collection_modifyitems(session, config, items):
        try:
            item_creator = CustomItem.from_parent  # Only available in pytest >= 5.4.0
        except AttributeError:
            item_creator = CustomItem

        items[:] = [item_creator(name=item.name, parent=item.parent) for item in items]

    class CustomItem(pytest.Item):
        def runtest(self):
            assert True
    """
    )

    pytester.makepyfile(
        """
    def test_convert_me_to_custom_item_and_assert_true():
        assert False
    """
    )

    result = pytester.runpytest()
    result.assert_outcomes(passed=1)


def test_pytest_bdd_after_scenario_called_after_scenario(pytester):
    """Regression test for https://github.com/pytest-dev/pytest-bdd/pull/577"""

    pytester.makefile(
        ".feature",
        foo=textwrap.dedent(
            """\
            Feature: A feature
                Scenario: Scenario 1
                    Given foo
                    When bar
                    Then baz

                Scenario: Scenario 2
                    When bar
                    Then baz
            """
        ),
    )

    pytester.makepyfile(
        """
    import pytest
    from pytest_bdd import given, when, then, scenarios


    scenarios("foo.feature")


    @given("foo")
    @when("bar")
    @then("baz")
    def _():
        pass
    """
    )

    pytester.makeconftest(
        """
    from pytest_bdd.utils import dump_obj

    def pytest_bdd_after_scenario(request, feature, scenario):
        dump_obj([feature, scenario])
    """
    )

    result = pytester.runpytest("-s")
    result.assert_outcomes(passed=2)

    hook_calls = collect_dumped_objects(result)
    assert len(hook_calls) == 2
    [(feature, scenario_1), (feature_2, scenario_2)] = hook_calls
    assert feature.name == feature_2.name == "A feature"

    assert scenario_1.name == "Scenario 1"
    assert scenario_2.name == "Scenario 2"


def test_pytest_unconfigure_without_configure(pytester):
    """
    Simulate a plugin forcing an exit during configuration before bdd is configured
    https://github.com/pytest-dev/pytest-bdd/issues/362
    """
    pytester.makeconftest(
        """
    import pytest

    def pytest_configure(config):
        pytest.exit("Exit during configure", 0)
        """
    )

    result = pytester.runpytest()
    assert result.ret == 0
