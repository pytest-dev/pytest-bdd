Feature: Handling quotes in code generation

    Scenario: A step definition with quotes should be escaped as needed
        Given I have a fixture with 'single' quotes
        And I have a fixture with "double" quotes
        And I have a fixture with single-quote '''triple''' quotes
        And I have a fixture with double-quote """triple""" quotes

        When I generate the code

        Then The generated string should be written
