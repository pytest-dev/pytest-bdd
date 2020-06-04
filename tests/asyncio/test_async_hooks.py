import textwrap

import pytest


@pytest.fixture
def feature_file(testdir):
    testdir.makefile(
        ".feature",
        test=textwrap.dedent(
            """
            Feature: Async hooks are being launched

                Scenario: Launching async hooks
                    Given i have step
                    And i have another step
            """
        ),
    )


@pytest.fixture
def hook_file(testdir):
    testdir.makeconftest(
        textwrap.dedent(
            """
            async def pytest_bdd_before_scenario(request, feature, scenario):
                print("\\npytest_bdd_before_scenario")

            async def pytest_bdd_after_scenario(request, feature, scenario):
                print("\\npytest_bdd_after_scenario")

            async def pytest_bdd_before_step(request, feature, scenario, step, step_func):
                print("\\npytest_bdd_before_step")

            async def pytest_bdd_before_step_call(request, feature, scenario, step, step_func, step_func_args):
                print("\\npytest_bdd_before_step_call")

            async def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
                print("\\npytest_bdd_after_step")

            async def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
                print("\\npytest_bdd_step_error")

            async def pytest_bdd_step_validation_error(request, feature, scenario, step, step_func, step_func_args,
                                                       exception):
                print("\\npytest_bdd_step_validation_error")

            async def pytest_bdd_step_func_lookup_error(request, feature, scenario, step, exception):
                print("\\npytest_bdd_step_func_lookup_error")
            """
        )
    )


def test_async_non_error_hooks_are_being_launched(feature_file, hook_file, testdir):
    testdir.makepyfile(
        textwrap.dedent(
            """
            import pytest
            from pytest_bdd import scenario, given

            @pytest.mark.asyncio
            @scenario('test.feature', 'Launching async hooks')
            def test_launching_async_hooks():
                pass

            @given("i have step")
            def i_have_step():
                pass
            """
        )
    )

    result = testdir.runpytest("-s")

    assert result.stdout.lines.count("pytest_bdd_before_scenario") == 1
    assert result.stdout.lines.count("pytest_bdd_after_scenario") == 1
    assert result.stdout.lines.count("pytest_bdd_before_step") == 1
    assert result.stdout.lines.count("pytest_bdd_before_step_call") == 1
    assert result.stdout.lines.count("pytest_bdd_after_step") == 1


def test_async_step_func_lookup_error_hook_is_being_launched(feature_file, hook_file, testdir):
    testdir.makepyfile(
        textwrap.dedent(
            """
            import pytest
            from pytest_bdd import scenario, given

            @pytest.mark.asyncio
            @scenario('test.feature', 'Launching async hooks')
            def test_launching_async_hooks():
                pass
            """
        )
    )

    result = testdir.runpytest("-s")

    assert result.stdout.lines.count("pytest_bdd_step_func_lookup_error") == 1


def test_async_step_error_hook_is_being_launched(feature_file, hook_file, testdir):
    testdir.makepyfile(
        textwrap.dedent(
            """
            import pytest
            from pytest_bdd import scenario, given

            @pytest.mark.asyncio
            @scenario('test.feature', 'Launching async hooks')
            def test_launching_async_hooks():
                pass

            @given("i have step")
            def i_have_step():
                raise Exception()
            """
        )
    )

    result = testdir.runpytest("-s")

    assert result.stdout.lines.count("pytest_bdd_step_error") == 1


def test_async_step_validation_error_hook_is_being_launched(hook_file, testdir):
    testdir.makefile(
        ".feature",
        test=textwrap.dedent(
            """
            Feature: Async hooks are being launched

                Scenario: Launching async hooks
                    Given i have step
                    And i have another step
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """
            import pytest
            from pytest_bdd import scenario, given

            @pytest.mark.asyncio
            @scenario('test.feature', 'Launching async hooks')
            def test_launching_async_hooks():
                pass

            @given("i have step")
            def i_have_step():
                pass

            @given("i have another step")
            def i_have_step():
                pass
            """
        )
    )

    result = testdir.runpytest("-s")

    assert result.stdout.lines.count("pytest_bdd_step_validation_error") == 1
