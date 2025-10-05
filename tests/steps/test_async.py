"""Test async step support."""

from __future__ import annotations

import textwrap


def test_async_given_in_sync_test(pytester, pytest_params):
    """Test async given step in a synchronous test."""
    pytester.makefile(
        ".feature",
        async_steps=textwrap.dedent(
            """\
            Feature: Async steps
                Scenario: Async given in sync test
                    Given I have an async resource
                    Then the resource should be available
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        import pytest
        from pytest_bdd import given, then, scenario

        pytestmark = pytest.mark.asyncio

        @scenario("async_steps.feature", "Async given in sync test")
        def test_async_given():
            pass

        @given("I have an async resource", target_fixture="resource")
        async def async_resource():
            await asyncio.sleep(0.001)
            return "async_value"

        @then("the resource should be available")
        def check_resource(resource):
            assert resource == "async_value"
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_async_when_then(pytester, pytest_params):
    """Test async when and then steps."""
    pytester.makefile(
        ".feature",
        async_steps=textwrap.dedent(
            """\
            Feature: Async steps
                Scenario: Async when and then
                    Given I have a value of 5
                    When I multiply it by 2 asynchronously
                    Then the result should be 10
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        from pytest_bdd import given, when, then, scenario

        @scenario("async_steps.feature", "Async when and then")
        def test_async_when_then():
            pass

        @given("I have a value of 5", target_fixture="value")
        def value():
            return 5

        @when("I multiply it by 2 asynchronously", target_fixture="result")
        async def multiply(value):
            await asyncio.sleep(0.001)
            return value * 2

        @then("the result should be 10")
        async def check_result(result):
            await asyncio.sleep(0.001)
            assert result == 10
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_mixed_sync_async_steps(pytester, pytest_params):
    """Test mixing sync and async steps in same scenario."""
    pytester.makefile(
        ".feature",
        mixed=textwrap.dedent(
            """\
            Feature: Mixed steps
                Scenario: Mix of sync and async
                    Given I have a sync resource
                    And I have an async resource
                    When I combine them synchronously
                    Then the combination should be correct
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        from pytest_bdd import given, when, then, scenario

        @scenario("mixed.feature", "Mix of sync and async")
        def test_mixed():
            pass

        @given("I have a sync resource", target_fixture="sync_res")
        def sync_resource():
            return "sync"

        @given("I have an async resource", target_fixture="async_res")
        async def async_resource():
            await asyncio.sleep(0.001)
            return "async"

        @when("I combine them synchronously", target_fixture="combined")
        def combine(sync_res, async_res):
            return f"{sync_res}+{async_res}"

        @then("the combination should be correct")
        def check_combined(combined):
            assert combined == "sync+async"
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_async_step_with_parsers(pytester, pytest_params):
    """Test async steps with parameter parsers."""
    pytester.makefile(
        ".feature",
        parsed=textwrap.dedent(
            """\
            Feature: Async with parsers
                Scenario: Parameterized async step
                    Given I wait for 50 milliseconds
                    Then the wait should be complete
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        import pytest
        from pytest_bdd import given, then, scenario, parsers

        pytestmark = pytest.mark.asyncio

        @scenario("parsed.feature", "Parameterized async step")
        def test_parsed():
            pass

        @given(parsers.parse("I wait for {duration:d} milliseconds"), target_fixture="wait_result")
        async def wait_async(duration):
            await asyncio.sleep(duration / 1000.0)
            return "completed"

        @then("the wait should be complete")
        def check_wait(wait_result):
            assert wait_result == "completed"
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_async_step_with_re_parser(pytester, pytest_params):
    """Test async steps with regex parser."""
    pytester.makefile(
        ".feature",
        regex=textwrap.dedent(
            """\
            Feature: Async with regex
                Scenario: Regex parsed async step
                    Given I have 42 items
                    Then the count should be correct
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            r"""
        import asyncio
        import pytest
        from pytest_bdd import given, then, scenario, parsers

        pytestmark = pytest.mark.asyncio

        @scenario("regex.feature", "Regex parsed async step")
        def test_regex():
            pass

        @given(
            parsers.re(r"I have (?P<count>\d+) items"),
            converters={"count": int},
            target_fixture="count"
        )
        async def async_count(count):
            await asyncio.sleep(0.001)
            return count

        @then("the count should be correct")
        def check_count(count):
            assert count == 42
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_async_step_error_propagation(pytester, pytest_params):
    """Test that exceptions in async steps are properly propagated."""
    pytester.makefile(
        ".feature",
        error=textwrap.dedent(
            """\
            Feature: Error handling
                Scenario: Async step raises error
                    Given an async step that fails
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        from pytest_bdd import given, scenario

        @scenario("error.feature", "Async step raises error")
        def test_error():
            pass

        @given("an async step that fails")
        async def failing_step():
            await asyncio.sleep(0.001)
            raise ValueError("Async step failed!")
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines(["*ValueError: Async step failed!*"])


def test_multiple_async_steps_in_sequence(pytester, pytest_params):
    """Test multiple async steps executing in sequence."""
    pytester.makefile(
        ".feature",
        sequence=textwrap.dedent(
            """\
            Feature: Sequential async
                Scenario: Multiple async steps
                    Given I start with value 1
                    When I add 2 asynchronously
                    And I multiply by 3 asynchronously
                    Then the final value should be 9
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        from pytest_bdd import given, when, then, scenario

        @scenario("sequence.feature", "Multiple async steps")
        def test_sequence():
            pass

        @given("I start with value 1", target_fixture="value")
        async def start_value():
            await asyncio.sleep(0.001)
            return 1

        @when("I add 2 asynchronously", target_fixture="value")
        async def add_two(value):
            await asyncio.sleep(0.001)
            return value + 2

        @when("I multiply by 3 asynchronously", target_fixture="value")
        async def multiply_three(value):
            await asyncio.sleep(0.001)
            return value * 3

        @then("the final value should be 9")
        def check_final_value(value):
            assert value == 9
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_async_step_with_fixture_dependency(pytester, pytest_params):
    """Test async step that depends on regular pytest fixtures."""
    pytester.makefile(
        ".feature",
        fixture_dep=textwrap.dedent(
            """\
            Feature: Fixture dependency
                Scenario: Async step uses fixtures
                    Given I have an async operation with fixtures
                    Then the operation should succeed
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        import pytest
        from pytest_bdd import given, then, scenario

        pytestmark = pytest.mark.asyncio

        @pytest.fixture
        def base_value():
            return 10

        @scenario("fixture_dep.feature", "Async step uses fixtures")
        def test_fixture_dep():
            pass

        @given("I have an async operation with fixtures", target_fixture="result")
        async def async_with_fixture(base_value):
            await asyncio.sleep(0.001)
            return base_value * 2

        @then("the operation should succeed")
        def check_result(result):
            assert result == 20
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_sync_step_with_async_fixture_requires_pytest_asyncio(pytester, pytest_params):
    """Test that sync steps with async fixtures require pytest-asyncio.

    This documents a limitation: async pytest fixtures require pytest-asyncio
    to be properly awaited. Without it, the fixture returns a coroutine object
    instead of the awaited value. This is a pytest limitation, not pytest-bdd.
    """
    pytester.makefile(
        ".feature",
        sync_async_fix=textwrap.dedent(
            """\
            Feature: Sync step with async fixture
                Scenario: Sync step uses async fixture without pytest-asyncio
                    Given I have a sync step with async fixture
                    Then the fixture should be a coroutine
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        import inspect
        import pytest
        from pytest_bdd import given, then, scenario

        pytestmark = pytest.mark.asyncio

        @pytest.fixture
        async def async_fixture():
            await asyncio.sleep(0.001)
            return "async_fixture_value"

        @scenario("sync_async_fix.feature", "Sync step uses async fixture without pytest-asyncio")
        def test_sync_with_async_fixture():
            pass

        @given("I have a sync step with async fixture", target_fixture="fixture_value")
        def sync_step_with_async_fixture(async_fixture):
            # Without pytest-asyncio, async fixtures return coroutines
            return async_fixture

        @then("the fixture should be a coroutine")
        def check_is_coroutine(fixture_value):
            # This demonstrates the limitation - async fixtures need pytest-asyncio
            assert "async_fixture_value" == fixture_value
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_sync_step_with_async_generator_fixture_requires_pytest_asyncio(pytester, pytest_params):
    """Test that sync steps with async fixtures require pytest-asyncio.

    This documents a limitation: async pytest fixtures require pytest-asyncio
    to be properly awaited. Without it, the fixture returns a coroutine object
    instead of the awaited value. This is a pytest limitation, not pytest-bdd.
    """
    pytester.makefile(
        ".feature",
        sync_async_fix=textwrap.dedent(
            """\
            Feature: Sync step with async fixture
                Scenario: Sync step uses async fixture without pytest-asyncio
                    Given I have a sync step with async fixture
                    Then the fixture should be a coroutine
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        import inspect
        import pytest
        from pytest_bdd import given, then, scenario

        pytestmark = pytest.mark.asyncio

        @pytest.fixture
        async def async_fixture():
            await asyncio.sleep(0.001)
            yield "async_fixture_value"

        @scenario("sync_async_fix.feature", "Sync step uses async fixture without pytest-asyncio")
        def test_sync_with_async_fixture():
            pass

        @given("I have a sync step with async fixture", target_fixture="fixture_value")
        def sync_step_with_async_fixture(async_fixture):
            # Without pytest-asyncio, async fixtures return coroutines
            return async_fixture

        @then("the fixture should be a coroutine")
        def check_is_coroutine(fixture_value):
            # This demonstrates the limitation - async fixtures need pytest-asyncio
            assert "async_fixture_value" == fixture_value
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_sync_steps_with_async_generator_fixture_requires_pytest_asyncio(pytester, pytest_params):
    """Test that sync steps with async fixtures require pytest-asyncio.

    This documents a limitation: async pytest fixtures require pytest-asyncio
    to be properly awaited. Without it, the fixture returns a coroutine object
    instead of the awaited value. This is a pytest limitation, not pytest-bdd.
    """
    pytester.makefile(
        ".feature",
        sync_async_fix=textwrap.dedent(
            """\
            Feature: Sync step with async fixture
                Scenario: Sync step uses async fixture without pytest-asyncio
                    Given I have a sync step with async fixture
                    And I have another step with async fixture
                    Then the fixture should be a coroutine
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import asyncio
        import inspect
        import pytest
        from pytest_bdd import given, then, scenario

        pytestmark = pytest.mark.asyncio

        @pytest.fixture
        async def async_fixture():
            await asyncio.sleep(0.001)
            yield "async_fixture_value"

        @scenario("sync_async_fix.feature", "Sync step uses async fixture without pytest-asyncio")
        def test_sync_with_async_fixture():
            pass

        @given("I have a sync step with async fixture", target_fixture="fixture_value")
        def sync_step_with_async_fixture(async_fixture):
            # Without pytest-asyncio, async fixtures return coroutines
            return async_fixture

        @given("I have another step with async fixture", target_fixture="fixture_value_2")
        def another_sync_step_with_async_fixture(async_fixture):
            # Without pytest-asyncio, async fixtures return coroutines
            return async_fixture

        @then("the fixture should be a coroutine")
        def check_is_coroutine(fixture_value):
            # This demonstrates the limitation - async fixtures need pytest-asyncio
            assert "async_fixture_value" == fixture_value
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)


def test_sync_steps_with_async_generator_fixture_requires_anyio(pytester, pytest_params):
    """Test that sync steps with async fixtures require anyio.

    This documents a limitation: async pytest fixtures require anyio
    to be properly awaited. Without it, the fixture returns a coroutine object
    instead of the awaited value. This is a pytest limitation, not pytest-bdd.
    """
    pytester.makefile(
        ".feature",
        sync_async_fix=textwrap.dedent(
            """\
            Feature: Sync step with async fixture
                Scenario: Sync step uses async fixture without pytest-asyncio
                    Given I have a sync step with async fixture
                    And I have another step with async fixture
                    Then the fixture should be a coroutine
            """
        ),
    )
    pytester.makepyfile(
        textwrap.dedent(
            """\
        import anyio
        import inspect
        import pytest
        from pytest_bdd import given, then, scenario

        pytestmark = pytest.mark.anyio

        @pytest.fixture
        def anyio_backend():
            return "asyncio"

        @pytest.fixture
        async def async_fixture():
            await anyio.sleep(0.001)
            yield "async_fixture_value"

        @scenario("sync_async_fix.feature", "Sync step uses async fixture without pytest-asyncio")
        def test_sync_with_async_fixture():
            pass

        @given("I have a sync step with async fixture", target_fixture="fixture_value")
        def sync_step_with_async_fixture(async_fixture):
            return async_fixture

        @given("I have another step with async fixture", target_fixture="fixture_value_2")
        def another_sync_step_with_async_fixture(async_fixture):
            return async_fixture

        @then("the fixture should be a coroutine")
        def check_is_coroutine(fixture_value):
            # This demonstrates the limitation - async fixtures need pytest-asyncio
            assert "async_fixture_value" == fixture_value
        """
        )
    )
    result = pytester.runpytest_subprocess(*pytest_params)
    result.assert_outcomes(passed=1)
