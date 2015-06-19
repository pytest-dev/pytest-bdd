Feature: When in background

    Background:
        Given I don't always write when after then, but
        When I do

    Scenario: When in background
    	Then its fine
    	When I do it again
    	Then its wrong
