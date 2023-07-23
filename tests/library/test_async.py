import textwrap


# TODO: Split this test in one that checks that we work correctly
# with the pytest-asyncio plugin, and another that checks that we correctly
# run async steps.
def test_async_steps(pytester):
    """Test parent given is collected.

    Both fixtures come from the parent conftest.
    """
    pytester.makefile(
        ".feature",
        async_feature=textwrap.dedent(
            """\
            Feature: A feature
                Scenario: A scenario
                    Given There is an async object

                    When I do an async action

                    Then the async object value should be "async_object"
                    And [async] the async object value should be "async_object"
                    And the another async object value should be "another_async_object"
            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, parsers, scenarios, then, when
        import asyncio
        import pytest

        scenarios("async_feature.feature")

        @pytest.fixture
        async def another_async_object():
            await asyncio.sleep(0.01)
            return "another_async_object"

        @given("There is an async object", target_fixture="async_object")
        async def given_async_obj():
            await asyncio.sleep(0.01)
            return "async_object"

        @when("I do an async action")
        async def when_i_do_async_action():
            await asyncio.sleep(0.01)

        @then(parsers.parse('the async object value should be "{value}"'))
        async def the_sync_object_value_should_be(async_object, value):
            assert async_object == value

        @then(parsers.parse('[async] the async object value should be "{value}"'))
        async def async_the_async_object_value_should_be(async_object, value):
            await asyncio.sleep(0.01)
            assert async_object == value

        @then(parsers.parse('the another async object value should be "{value}"'))
        def the_another_async_object_value_should_be(another_async_object, value):
            assert another_async_object == value

        """
        )
    )
    result = pytester.runpytest("--asyncio-mode=auto")
    result.assert_outcomes(passed=1)
