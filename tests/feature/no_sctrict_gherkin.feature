Feature: No strict Gherkin Background support

    Background:
        When foo has a value "bar"
        And foo is not boolean
        And foo has not a value "baz"
        Then foo has length equal 1

    Scenario: Test background
