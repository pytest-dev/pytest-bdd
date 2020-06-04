import textwrap

import pytest


@pytest.fixture
def feature_file(testdir):
    testdir.makefile(
        ".feature",
        test=textwrap.dedent(
            """
            Feature: Async scenario function is being launched

                Scenario: Launching scenario function
            """
        ),
    )


def test_scenario_function_marked_with_async_passes(feature_file, testdir):
    testdir.makepyfile(
        textwrap.dedent(
            """
            import pytest
            from pytest_bdd import scenario

            @pytest.mark.asyncio
            @scenario('test.feature', 'Launching scenario function')
            async def test_launching_scenario_function():
                pass
            """
        )
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


PYTEST_VERSION = tuple([int(i) for i in pytest.__version__.split(".")])


@pytest.mark.skipif(
    PYTEST_VERSION < (5, 1, 0),
    reason="Async functions not marked as @pytest.mark.asyncio are silently passing on pytest < 5.1.0",
)
def test_scenario_function_not_marked_with_async_fails(feature_file, testdir):
    testdir.makepyfile(
        textwrap.dedent(
            """
            import pytest
            from pytest_bdd import scenario

            @scenario('test.feature', 'Launching scenario function')
            async def test_launching_scenario_function():
                pass
            """
        )
    )

    result = testdir.runpytest()
    result.assert_outcomes(failed=1)
