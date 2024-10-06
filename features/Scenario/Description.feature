Feature: Descriptions
  Free-form descriptions can be placed
  underneath Feature, Example/Scenario, Background, Scenario Outline and Rule.
  You can write anything you like, as long as no line starts with a keyword.
  Descriptions can be in the form of Markdown - formatters including
  the official HTML formatter support this.

  Scenario:
      Given File "Description.feature" with content:
        """gherkin
        Feature:
          Scenario:
            My Scenario description

            Given I check scenario description
        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd import given

        @given('I check scenario description')
        def step(scenario):
          assert "My Scenario description" in scenario.description
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     0|
