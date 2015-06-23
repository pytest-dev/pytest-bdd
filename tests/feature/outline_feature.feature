Feature: Outline

    Examples:
    | start | eat | left |
    |  12   |  5  |  7   |
    |  5    |  4  |  1   |

    Scenario Outline: Outlined given, when, thens
        Given there are <start> cucumbers
        When I eat <eat> cucumbers
        Then I should have <left> cucumbers
