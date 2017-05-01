Feature: No strict Gherkin Scenario support

    Scenario: Test scenario
        When foo has a value "bar"
        And foo is not boolean
        And foo has not a value "baz"
