Scenario: When after then
	Given I don't always write when after then, but
	When I do
	Then its fine
	When I do it again
	Then its wrong


Scenario: Then first
	Then it won't work


Scenario: Given after When
	Given something
	When something else
	Given won't work


Scenario: Given after Then
	Given something
	When something else
	Then nevermind
	Given won't work
