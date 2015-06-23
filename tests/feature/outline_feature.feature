Feature: Outline

    Examples:
    | start | eat | left |
    |  12   |  5  |  7   |
    |  5    |  4  |  1   |

    Scenario Outline: Outlined given, when, thens
        Given there are <start> <fruits>
        When I eat <eat> <fruits>
        Then I should have <left> <fruits>

        Examples:
        | fruits  |
        | oranges |
        | apples  |
