Feature: Datatables with colliding datatables
  As a pytest-bdd user I want to be sure there won't
  be collisions with other fixtures named datatable

  Scenario: Ensure that there is an existing datatable fixture
    Given There is an existing fixture named datatable
    Then datatable contents match existing fixture


  Scenario: Ensure that datatable does not conflict with existing fixture
    Given There is an existing fixture named datatable
    And I have the following cars:
      | make   | model     | year |
      | Honda  | Accord    | 2010 |
      | Ford   | Ranger    | 1992 |
      | Toyota | Cressida  | 1989 |
      | Ford   | Econoline | 1987 |
      | Toyota | Corolla   | 2012 |
    Then datatable contents don't match existing fixture
    And I should see the following models:
      | model     |
      | Accord    |
      | Ranger    |
      | Cressida  |
      | Econoline |
      | Corolla   |


