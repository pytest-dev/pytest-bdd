Feature: Gherkin terminal reporter

  Scenario: Should default output be the same as regular terminal reporter
    Given there is gherkin scenario implemented
    When tests are run
    Then output must be formatted the same way as regular one

  Scenario: Should verbose mode enable displaying feature and scenario names rather than test names in a single line
    Given there is gherkin scenario implemented
    When tests are run with verbose mode
    Then output should contain single line feature description
    And output should contain single line scenario description

  Scenario: Should verbose mode preserve displaying of regular tests as usual
    Given there is non-gherkin scenario implemented
    When tests are run with verbose mode
    Then output must be formatted the same way as regular one

  Scenario: Should double verbose mode enable displaying of full gherkin scenario description
    Given there is gherkin scenario implemented
    When tests are run with very verbose mode
    Then output must contain full gherkin scenario description

  Scenario: Should error message be displayed when no scenario is found
    Given there is gherkin scenario without implementation
    When tests are run with any verbosity mode
    Then output contains error about missing scenario implementation

  Scenario: Should error message be displayed when no step is found
    Given there is gherkin scenario partially implemented
    When tests are run with any verbosity mode
    Then output contains error about missing step implementation

  Scenario: Should error message be displayed when error occurs during test execution
    Given there is gherkin scenario with broken implementation
    When tests are run with any verbosity mode
    Then output contains error about missing scenario implementation

  Scenario: Should local variables be displayed when --showlocals option is used
    Given there is gherkin scenario with broken implementation
    When tests are run with --showlocals
    Then error traceback contains local variable descriptions

  Scenario: Should step parameters be replaced by their values
    Given there is gherkin scenario outline implemented
    When tests are run with step expanded mode
    Then output must contain parameters values
