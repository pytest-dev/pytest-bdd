Feature: NDJson could be produced on the feature run
  Scenario:
    Given File "Passing.feature" with content:
        """gherkin
        Feature: Passing feature
          Scenario: Passing scenario
            Given Passing step
        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd import step

        collect_ignore_glob = ["*.lock"]  # Workaround to allow launch this test under Gherkin itself

        @step('Passing step')
        def _():
          ...
        """
      When run pytest
        |cli_args  |--messagesndjson|out.ndjson|
      Then File "out.ndjson" has "15" lines
      Then Report "out.ndjson" parsable into messages
