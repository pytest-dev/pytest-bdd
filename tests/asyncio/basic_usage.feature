Feature: Basic usage of asynchronous steps

  Scenario: Launching app in task
    Given i have launched app
    When i post input variable to have value of 3
    And i wait 1 second(s)
    Then output value should be equal to 4
