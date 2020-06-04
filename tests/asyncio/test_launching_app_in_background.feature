Feature: Launching application in async task

  Scenario: App is running during whole scenario
    Given i have launched app
    When i post input variable to have value of 3
    Then output value should be equal to 4
