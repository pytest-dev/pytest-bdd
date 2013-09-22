Scenario: Given and when using the same fixture should not evaluate it twice
	Given I have an empty list
	
	# Alias of the "I have a fixture (appends 1 to a list)"
	And I have a fixture (appends 1 to a list) in reuse syntax
	
	When I use this fixture
	Then my list should be [1]
