Scenario: Every step takes a parameter with the same name
	Given I have 1 Euro
	When I pay 2 Euro
	And I pay 1 Euro
	Then I should have 0 Euro
	And I should have 999999 Euro # In my dream...


Scenario: Using the same given fixture raises an error
	Given I have 1 Euro
	And I have 2 Euro


Scenario: Test argumented step
    Given I buy 5 red apples

    Then I should have 5 red apples


Scenario: Test function argument cleanup
    Given I have 2 apples

    Then I should have 2 apples

