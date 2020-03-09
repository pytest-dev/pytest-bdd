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
