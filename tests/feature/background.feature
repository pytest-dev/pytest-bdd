Feature: Background support

    Background:
        Given foo has a value "bar"
        And a background step with multiple lines:
          one
          two

    Scenario: Basic usage
        Then foo should have value "bar"

    Scenario: Background steps are executed first
        Given foo has no value "bar"
        And foo has a value "dummy"

        Then foo should have value "dummy"
        And foo should not have value "bar"
