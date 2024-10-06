Feature: Gherkin features load by scenario and scenarios functions

  Rule:
    Background:
      Given File "Passing.feature" in the temporary path with content:
        """gherkin
        Feature: Passing feature
          Scenario: Passing scenario
            Given Passing step
        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd import step

        @step('Passing step')
        def _():
          ...
        """

    Scenario: "scenario" function is used as decorator
      And File "test_scenario_load.py" with fixture templated content:
        """python
        from pytest_bdd import scenario
        from pathlib import Path

        @scenario(Path(r"{tmp_path}") / "Passing.feature")
        def test_passing_feature():
          # It is however encouraged to try as much as possible to have your logic only inside the Given, When, Then steps.
          ...
        """

    Scenario: "scenarios" function is used as decorator
      And File "test_scenario_load.py" with fixture templated content:
        """python
        from pytest_bdd import scenarios
        from pathlib import Path

        @scenarios(Path(r"{tmp_path}") / "Passing.feature", return_test_decorator=True)
        def test_passing_feature():
          # It is however encouraged to try as much as possible to have your logic only inside the Given, When, Then steps.
          ...
        """

      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|

    Scenario: "scenario" function is used to register feature as test
      And File "test_scenario_load.py" with fixture templated content:
        """python
        from pytest_bdd import scenario
        from pathlib import Path

        test_passing_feature = scenario(Path(r"{tmp_path}") / "Passing.feature", return_test_decorator=False)
        """

      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|

    Scenario: "scenarios" function is used to register feature as test
      And File "test_scenario_load.py" with fixture templated content:
        """python
        from pytest_bdd import scenarios
        from pathlib import Path

        test_passing_feature = scenarios(Path(r"{tmp_path}") / "Passing.feature")
        """

      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|
