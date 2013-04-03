"""Tests for pytest-bdd-splinter subplugin."""


def test_pytest_scenario(testdir):
        testdir.maketxtfile(**{'some_feature': """
Scenario: Test some feature
    Given I have an event
    And the merchant has a backoffice user

    When I am at the event dashboard page
    And I click the copy event button

    Then I should not see an error message
    And the event name should start with Copy of
        """})

        testdir.makepyfile("""
            import pytest
            from pytest_bdd import scenario, given, when, then

            test_scenario = scenario('some_feature.txt', 'Test some feature')

            @given('I have an event')
            @pytest.fixture
            def event():
                return object()


            @given('the merchant has a backoffice user')
            @pytest.fixture
            def merchant_user():
                return 'some user'


            @pytest.fixture
            def browser():
                return object()


            @pytest.fixture
            def backoffice_browser(browser):
                return object()


            @when('I am at the event dashboard page')
            def i_go_to_event(event, backoffice_browser):
                pass


            @when('I click the copy event button')
            def click_copy_event(event, browser):
                pass


            @then('I should not see an error message')
            def i_should_not_see_an_error(browser):
                assert True


            @then('the event name should start with Copy of')
            def event_name_should_start_with_copy_of(browser):
                assert True

        """)
        result = testdir.runpytest("-v")
        result.stdout.fnmatch_lines([
            "*test_scenario*PASS*",
        ])
