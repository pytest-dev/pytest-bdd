Feature: Step realization could match broad step keywords
  """
  Same step could be used for all types of steps without re-defining alias;
  this step could be used with any keyword"""
  Background:
    Given File "liberal_steps.feature" with content:
      # language=gherkin
      """
      Feature: Steps are executed one by one
        All steps could be executed by "step" matcher

        Scenario: Executed step by step
            Given I execute foo step
            And I execute bar step
            When I execute fizz step
            But I execute buzz step
            Then I execute nice step
            * I execute good step

            Then Steps were executed:
              |foo|bar|fizz|buzz|nice|good|
      """
    Scenario Outline: Step execution with liberal matcher
      And File "conftest.py" with content:
          # language=python
          """
          from pytest_bdd import step
          from pytest import fixture
          from operator import attrgetter

          @fixture
          def step_values():
              return []

          @step('I execute {value} step', liberal=True)
          def foo(step_values, value):
              step_values.append(value)

          @step("Steps were executed:")
          def check_steps(step_values, step):
              oracle_values = map(attrgetter("value"), step.data_table.rows[0].cells)
              for oracle_value in oracle_values:
                  assert oracle_value in step_values
          """

      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     0|

    Scenario: Step execution with keyworded liberal matcher
      And File "conftest.py" with content:
          # language=python
          """
          from pytest_bdd import given, then
          from pytest import fixture
          from operator import attrgetter

          @fixture
          def step_values():
              return []

          @given('I execute {value} step', liberal=True)
          def foo(step_values, value):
              step_values.append(value)

          @then("Steps were executed:")
          def check_steps(step_values, step):
              oracle_values = map(attrgetter("value"), step.data_table.rows[0].cells)
              for oracle_value in oracle_values:
                  assert oracle_value in step_values
          """

      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     0|

    Rule: Keyworded steps could be treated as liberal by pytest command line option
      Background:
        And File "conftest.py" with content:
            # language=python
            """
            from pytest_bdd import given, then
            from pytest import fixture
            from operator import attrgetter

            @fixture
            def step_values():
                return []

            @given('I execute {value} step')
            def foo(step_values, value):
                step_values.append(value)

            @then("Steps were executed:")
            def check_steps(step_values, step):
                oracle_values = map(attrgetter("value"), step.data_table.rows[0].cells)
                for oracle_value in oracle_values:
                    assert oracle_value in step_values
            """

      Example: With argument
        When run pytest
          |cli_args| --liberal-steps|
        Then pytest outcome must contain tests with statuses:
          |passed|failed|
          |     1|     0|

      Example: Without argument
        When run pytest
        Then pytest outcome must contain tests with statuses:
          |passed|failed|
          |     0|     1|
