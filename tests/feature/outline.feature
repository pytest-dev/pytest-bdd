Scenario Outline: Outlined given, when, thens
    Given there are <start> cucumbers
    When I eat <eat> cucumbers
    Then I should have <left> cucumbers

    Examples:
    | start | eat | left |
    |  12   |  5  |  7   |


Scenario Outline: Outlined with wrong examples
    Given there are <start> cucumbers
    When I eat <eat> cucumbers
    Then I should have <left> cucumbers

    Examples:
    | start | eat | left | unknown_param |
    |  12   |  5  |  7   | value         |


Scenario Outline: Outlined with some examples failing
    Given there are <start> cucumbers
    When I eat <eat> cucumbers
    Then I should have <left> cucumbers

    Examples:
    | start | eat | left |
    |  0    |  5  |  5   |
    |  12   |  5  |  7   |
