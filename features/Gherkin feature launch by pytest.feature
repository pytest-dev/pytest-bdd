Feature: Gherkin execution by pytest runner
  Scenario: Sequential steps execution
    Given File "steps.feature" with content:
      # language=gherkin
      """
      Feature: Steps are executed one by one
        Steps are executed one by one. Given and When sections are not mandatory in some cases.

        Scenario: Executed step by step
            * I have some precondition
            Given I have a foo fixture with value "foo"
            And there is a list
            When I append 1 to the list
            And I append 2 to the list
            And I append 3 to the list
            Then foo should have value "foo"
            But the list should be [1, 2, 3]
      """
    And File "conftest.py" with content:
        # Here is examples of step matchers to be used during Feature execution
        # language=python
        """
        from pytest_bdd import given, when, then, step

        @step('I have some precondition')
        def setup_preconditon():
          ...

        @given('I have a foo fixture with value "foo"', target_fixture="foo")
        def foo():
            return "foo"

        @given("there is a list", target_fixture="results")
        def results():
            return []

        @when("I append 1 to the list")
        def append_1(results):
            results.append(1)

        @when("I append 2 to the list")
        def append_2(results):
            results.append(2)

        @when("I append 3 to the list")
        def append_3(results):
            results.append(3)

        @then('foo should have value "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"

        @then("the list should be [1, 2, 3]")
        def check_results(results):
            assert results == [1, 2, 3]
        """

    When run pytest
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
