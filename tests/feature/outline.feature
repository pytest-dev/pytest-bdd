Scenario Outline: Outlined given, when, thens
    Given there are <start> cucumbers
    When I eat <eat> cucumbers
    Then I should have <left> cucumbers

    Examples:
    | start | eat | left |
    |  12   |  5  |  7   |
    |  5    |  4  |  1   |


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


Scenario Outline: Outlined with vertical example table
    Given there are <start> cucumbers
    When I eat <eat> cucumbers
    Then I should have <left> cucumbers

    Examples: Vertical
    | start | 12 | 2 |
    | eat   | 5  | 1 |
    | left  | 7  | 1 |


Scenario Outline: Outlined with empty example values vertical
    Given there are <start> cucumbers
    When I eat <eat> cucumbers
    Then I should have <left> cucumbers

    Examples: Vertical
    | start | # |
    | eat   |   |
    | left  |   |


Scenario Outline: Outlined with empty example values
    Given there are <start> cucumbers
    When I eat <eat> cucumbers
    Then I should have <left> cucumbers

    Examples:
    | start | eat | left |
    | #     |     |      |
