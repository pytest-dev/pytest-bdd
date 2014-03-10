Feature: Multiline step using sub indentation
	Given I have a step with:
		Some 
		Extra
		Lines
	Then text should be parsed with correct indentation
