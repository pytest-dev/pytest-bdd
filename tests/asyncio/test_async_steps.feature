Feature: Async steps

  Scenario: Async steps are actually executed
    Given i have async step
    When i do async step
    Then i should have async step

  Scenario: Async steps are executed along with regular steps
    Given i have async step
    And i have regular step

    When i do async step
    And i do regular step

    Then i should have async step
    And i should have regular step
