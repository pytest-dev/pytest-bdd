Scenario: Test reusing root fixture
	Given I have an alias to the root fixture
	Then root should be "root"


Scenario: Test reusing local fixture
	Given I have alias for foo
	Then foo should be "foo"
