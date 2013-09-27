Scenario: Multiple given alias is not evaluated multiple times
	Given I have an empty list
	
	# Alias of the "I have foo (which is 1) in my list"
	And I have bar (alias of foo) in my list
	
	When I do crash (which is 2)
	And I do boom (alias of crash)
	Then my list should be [1, 2, 2]
