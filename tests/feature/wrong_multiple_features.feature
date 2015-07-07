Feature: Feature One

  Background:
    Given I have A
    And I have B

  Scenario: Do something with A
    When I do something with A
    Then something about B

Feature: Feature Two

  Background:
    Given I have A

  Scenario: Something that just needs A
    When I do something else with A
    Then something else about B

  Scenario: Something that needs B again
    Given I have B
    When I do something else with B
    Then something else about A and B
