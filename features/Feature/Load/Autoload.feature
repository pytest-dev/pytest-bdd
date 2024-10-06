Feature: Gherkin features autoload
  By default gherkin features are autoloaded and treated as usual pytest tests
  if are placed in the tests hierarchy proposed by pytest.
  This behavior could be disabled

  Rule: Feature autoload
    Background:
      Given File "Passing.feature" with content:
        """gherkin
        Feature: Passing feature
          Scenario: Passing scenario
            * Passing step
        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd import step

        @step('Passing step')
        def plain_step():
          ...
        """
    Scenario: Feature is loaded by default
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|

    Scenario: Feature autoload could be disabled via command line
      When run pytest
        |cli_args|--disable-feature-autoload|
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     0|

    Scenario: Feature autoload could be disabled via pytest.ini
      Given Set pytest.ini content to:
        """ini
        [pytest]
        disable_feature_autoload=true
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     0|
