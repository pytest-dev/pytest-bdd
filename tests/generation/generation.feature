Feature: Missing code generation

    Background:
        Given I have a foobar

    Scenario: Scenario tests which are already bound to the tests stay as is
        Given I have a bar


    Scenario: Code is generated for scenarios which are not bound to any tests
        Given I have a bar

    Scenario: Scenario tests which are already bound to the tests stay as is, with parser
        Given I have 20 bars

    Scenario: Code is generated for scenario steps which are not yet defined(implemented)
        Given I have a custom bar
