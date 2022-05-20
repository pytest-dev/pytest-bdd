Feature: Scenario
  Scenario: Simple passed scenario
    Given example.feature with content:
      """
      Feature: Scenario
        Scenario: Simple passed example
          Given passed step
          When passed step
          Then passed step
      """
    And example_test.py with content:
      """
      from pytest_bdd import scenario
      from pytest_bdd import given, then, when

      @given("passed step")
      def given_passed_step():
          pass

      @when("passed step")
      @then("passed step")
      def passed_step():
          pass

      @scenario("example.feature", "Simple passed example")
      def test_scenario_example():
          pass
      """
    When run pytest-bdd with allure
    Then allure report has result for "Simple passed example" scenario
    Then this scenario has passed status
    Then this scenario has a history id
