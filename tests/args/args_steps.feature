Feature: Arguments step
    Scenario: Every step takes a parameter with the same name
        Given I have 1 Euro
        When I pay 2 Euro
        And I pay 1 Euro
        Then I should have 0 Euro
        # In my dream...
        And I should have 999999 Euro

    Scenario: Using the same given fixture raises an error
        Given I have 1 Euro
        And I have 2 Euro
