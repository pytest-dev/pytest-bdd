Feature: Outline

    Examples:
    | first | consume | remaining |
    |  12   |  5      |  7        |
    |  5    |  4      |  1        |

    Scenario Outline: Outlined modern given, when, thens
        Given there were <first> <foods>
        When I ate <consume> <foods>
        Then I should have had <remaining> <foods>

        Examples:
        | foods      |
        | ice-creams |
        | almonds    |
