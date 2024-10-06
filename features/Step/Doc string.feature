Feature: Steps could have docstrings

  Scenario:
      Given File "Steps.feature" with content:
        """gherkin
        Feature:
          Scenario:
            Given I check step docstring
              ```
              Step docstring
              ```

        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd import given

        @given('I check step docstring')
        def _(step):
          assert step.doc_string.content == "Step docstring"
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     0|
