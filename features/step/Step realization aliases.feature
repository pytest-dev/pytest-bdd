Feature: Step realization matchers could be defined multiple times
  """
  Sometimes, one has to declare the same fixtures or steps with
  different names for better readability. In order to use the same step
  function with multiple step names simply decorate it multiple times.
  """
  Scenario: Step execution with aliases
    Given File "alias.feature" with content:
      # language=gherkin
      """
      Feature: StepHandler aliases
        Scenario: Multiple step aliases
          Given I have an empty list
          And I have foo (which is 1) in my list
          # Alias of the "I have foo (which is 1) in my list"
          And I have bar (alias of foo) in my list

          When I do crash (which is 2)
          And I do boom (alias of crash)
          Then my list should be [1, 1, 2, 2]

      """
    And File "conftest.py" with content:
        # language=python
        """
        from pytest_bdd import given, when, then

        @given("I have an empty list", target_fixture="results")
        def results():
            return []

        @given("I have foo (which is 1) in my list")
        @given("I have bar (alias of foo) in my list")
        def foo(results):
            results.append(1)

        @when("I do crash (which is 2)")
        @when("I do boom (alias of crash)")
        def crash(results):
            results.append(2)

        @then("my list should be [1, 1, 2, 2]")
        def check_results(results):
            assert results == [1, 1, 2, 2]
        """

    When run pytest
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
