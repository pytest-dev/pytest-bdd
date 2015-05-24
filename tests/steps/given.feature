Scenario: Test reusing root fixture
	Given I have an alias to the root fixture
	Then root should be "root"


Scenario: Test reusing local fixture
	Given I have alias for foo
	Then foo should be "foo"


Scenario: Test session given
    Given I have session foo
    Then session foo should be "session foo"


Scenario: Test given fixture injection
    Given I have injecting given
    Then foo should be "injected foo"
