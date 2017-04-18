Feature: No strict Gherkin Background support

    Background:
        When foo has a value "bar"
        And foo is not boolean
        And foo has not a value "baz"

    Scenario: Test background
