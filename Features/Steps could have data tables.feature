Feature: Steps could have docstrings

  Scenario:
      Given File "Steps.feature" with content:
        """gherkin
        Feature:
          Scenario:
            Given I check step datatable
              |first|second|
              |    a|     b|

        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd import given
        from messages import Step

        def get_datatable_row_values(row):
          return list(map(lambda cell: cell.value, row.cells))

        @given('I check step datatable')
        def _(step: Step):
          title_row, *data_rows = step.data_table.rows
          assert get_datatable_row_values(title_row) == ["first", "second"]
          assert get_datatable_row_values(data_rows[0]) == ["a", "b"]
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     0|
