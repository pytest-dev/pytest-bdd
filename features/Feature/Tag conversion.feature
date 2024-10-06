Feature: Scenarios tags could be converted via hooks

  Scenario:
      Given File "Passed.feature" with content:
        """gherkin
        Feature:
          @todo
          Scenario: Failed
            Given I produce failed test

          Scenario: Passed
            Given I produce passed test
        """
      And File "conftest.py" with content:
        """python
        import pytest
        from pytest_bdd import given
        from pytest_bdd.compatibility.pytest import fail

        def pytest_bdd_convert_tag_to_marks(feature, scenario, tag):
          if tag == 'todo':
             marker = pytest.mark.skip(reason="Not implemented yet")
             return [marker]

        @given('I produce passed test')
        def passing_step():
          ...

        @given('I produce failed test')
        def failing_step():
          fail('Enforce fail')

        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|failed|skipped|
        |     1|     0|      1|
