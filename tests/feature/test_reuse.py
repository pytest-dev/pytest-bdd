"""Steps using the same fixture should not evaluate it twice."""

import textwrap


def test_reuse_fixture(testdir):
    testdir.makefile(
        ".feature",
        reuse=textwrap.dedent(
            """\
            Feature: Reusing fixtures
                Scenario: Steps using the same fixture should not evaluate it twice
                    Given I have an empty list

                    # Alias of the "I have a fixture (appends 1 to a list)"
                    And I have a fixture (appends 1 to a list) in reuse syntax

                    When I use this fixture
                    Then my list should be [1]

            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given, when, then, scenario

        @scenario("reuse.feature", "Steps using the same fixture should not evaluate it twice")
        def test_reuse():
            pass


        @given("I have an empty list")
        def empty_list():
            return []


        @given("I have a fixture (appends 1 to a list)")
        def appends_1(empty_list):
            empty_list.append(1)
            return empty_list


        given("I have a fixture (appends 1 to a list) in reuse syntax", fixture="appends_1")


        @when("I use this fixture")
        def use_fixture(appends_1):
            pass


        @then("my list should be [1]")
        def list_should_be_1(appends_1):
            assert appends_1 == [1]

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 0
