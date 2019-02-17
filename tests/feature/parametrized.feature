Scenario: Parametrized given, when, thens
    Given there are <start> cucumbers
    When I eat <eat> cucumbers
    Then I should have <left> cucumbers


Scenario: Parametrized given, then - single parameter name
    Given there are <start> cucumbers
    When I do not eat any cucumber
    Then I still should have <start> cucumbers
