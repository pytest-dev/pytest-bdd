Feature: Simple project tests that use pytest-bdd-ng could be run via pytest
  Project per se: https://github.com/elchupanebrej/pytest-bdd-ng/tree/default/docs/tutorial

  Scenario: Catalog example with simplest steps
    Given Copy path from "docs/tutorial" to test path "tutorial"
    When run pytest
      |cli_args| --rootdir=tutorial| tutorial/tests |
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
