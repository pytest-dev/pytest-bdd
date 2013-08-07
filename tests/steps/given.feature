Scenario: Test reusing root fixture
	Given I have an alias to the root fixture
	Then root should be "root"


Scenario: Test reusing local fixture
	Given I have alias for foo
	Then foo should be "foo"

Scenario: Test of using list of fixtures with given
    Given I have a given with list of foo and bar fixtures

    Then foo should be "foo"
    And bar should be "bar"