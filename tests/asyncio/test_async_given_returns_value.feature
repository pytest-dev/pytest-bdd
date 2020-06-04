Feature: Async given is a fixture and its value is properly returned

  Scenario: Async given shadows fixture
    Given i have given that shadows fixture with value of 42
    Then shadowed fixture value should be equal to 42

  Scenario: Async given is a fixture
    Given i have given that is a fixture with value of 42
    Then value of given as a fixture should be equal to 42
