"""Test scenarios shortcut."""
import textwrap

from tests.utils import assert_outcomes


def test_scenarios(testdir, pytest_params):
    """Test scenarios shortcut (used together with @scenario for individual test override)."""
    testdir.makeini(
        """
            [pytest]
            console_output_style=classic
        """
    )
    testdir.makeconftest(
        """
        import pytest
        from pytest_bdd import given

        import anyio

        @given('I have a bar')
        async def i_have_bar():
            await anyio.sleep(0)
            print('bar!')
            return 'bar'
    """
    )
    features = testdir.mkdir("features")
    features.join("test.feature").write_text(
        textwrap.dedent(
            """
    @anyio
    Scenario: Test scenario
        Given I have a bar
    """
        ),
        "utf-8",
        ensure=True,
    )
    features.join("subfolder", "test.feature").write_text(
        textwrap.dedent(
            """
    @anyio
    Scenario: Test subfolder scenario
        Given I have a bar

    @anyio
    Scenario: Test failing subfolder scenario
        Given I have a failing bar

    @anyio
    Scenario: Test already bound scenario
        Given I have a bar

    @anyio
    Scenario: Test scenario
        Given I have a bar
    """
        ),
        "utf-8",
        ensure=True,
    )
    testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import async_scenarios, async_scenario

        @pytest.mark.anyio
        @async_scenario('features/subfolder/test.feature', 'Test already bound scenario')
        async def test_already_bound():
            pass

        async_scenarios('features')
    """
    )
    result = testdir.runpytest_subprocess("-v", "-s", *pytest_params)
    assert_outcomes(result, passed=8, failed=2)
    result.stdout.fnmatch_lines(["*collected 10 items"])
    result.stdout.fnmatch_lines(["*test_test_subfolder_scenario[[]asyncio[]] *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_subfolder_scenario[[]trio[]] *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario[[]asyncio[]] *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario[[]trio[]] *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_failing_subfolder_scenario[[]asyncio[]] *FAILED"])
    result.stdout.fnmatch_lines(["*test_test_failing_subfolder_scenario[[]trio[]] *FAILED"])
    result.stdout.fnmatch_lines(["*test_already_bound[[]asyncio[]] *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_already_bound[[]trio[]] *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario_1[[]asyncio[]] *bar!", "PASSED"])
    result.stdout.fnmatch_lines(["*test_test_scenario_1[[]trio[]] *bar!", "PASSED"])


def test_scenarios_none_found(testdir, pytest_params):
    """Test scenarios shortcut when no scenarios found."""
    testpath = testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import async_scenarios

        async_scenarios('.')
    """
    )
    result = testdir.runpytest_subprocess(testpath, *pytest_params)
    assert_outcomes(result, errors=1)
    result.stdout.fnmatch_lines(["*NoScenariosFound*"])
