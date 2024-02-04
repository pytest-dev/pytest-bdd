Feature: Tutorial examples could be executed successfully

  Scenario: Catalog example with simplest steps
    Given Copy path from "docs/tutorial" to test path "tutorial"
    When run pytest
      |cli_args| --rootdir=tutorial| tutorial/tests |

    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
