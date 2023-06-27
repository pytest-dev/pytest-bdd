Feature: Scenario Outline examples could be tagged
  Rule:
    Background:
      Given File "steps.feature" with content:
        """gherkin
        Feature: Steps are executed by corresponding step keyword decorator

          Scenario Outline:
              Given I produce <outcome> test

              @passed
              Examples:
              |outcome|
              |passed |

              @failed
              Examples:
              |outcome|
              |failed |

              @both
              Examples:
              |outcome|
              |passed |
              |failed |
        """
      Given File "pytest.ini" with content:
        """ini
        [pytest]
        markers =
          passed
          failed
          both
        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd.compatibility.pytest import fail
        from pytest_bdd import given

        @given('I produce passed test')
        def passing_step():
          ...

        @given('I produce failed test')
        def failing_step():
          fail('Enforce fail')
        """
    Example:
      When run pytest
        |cli_args|-m|passed|
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     0|

    Example:
      When run pytest
        |cli_args|-m|failed|
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     0|     1|

    Example:
      When run pytest
        |cli_args|-m|passed or failed|
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     1|

    Example:
      When run pytest
        |cli_args|-m|not both|
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     1|

    Example:
      When run pytest
        |cli_args|-m|both|
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     1|

    Example:
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     2|     2|

  Rule: Mixing tags on feature & examples level
    Background:
      Given File "steps.feature" with content:
        """gherkin
        @feature_tag
        Feature: Steps are executed by corresponding step keyword decorator

          Scenario Outline:
              Given I produce <outcome> test

              Examples:
              |outcome|
              |passed |

              @examples_tag
              Examples:
              |outcome|
              |failed |
        """
      Given File "pytest.ini" with content:
        """ini
        [pytest]
        markers =
          feature_tag
          examples_tag
        """
      And File "conftest.py" with content:
        """python
        from pytest_bdd.compatibility.pytest import fail
        from pytest_bdd import given

        @given('I produce passed test')
        def passing_step():
          ...

        @given('I produce failed test')
        def failing_step():
          fail('Enforce fail')
        """
    Example:
      When run pytest
        |cli_args|-m|feature_tag|
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     1|

    Example:
      When run pytest
        |cli_args|-m|examples_tag|
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     0|     1|

    Example:
      When run pytest
        |cli_args|-m|not feature_tag|
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     0|     0|

    Example:
      When run pytest
        |cli_args|-m|not examples_tag|
      Then pytest outcome must contain tests with statuses:
        |passed|failed|
        |     1|     0|

    Example:
      When run pytest
        |cli_args|-m|feature_tag|--collect-only|
      Then pytest outcome must match lines:
        |collected 2 items|

    Example:
      When run pytest
        |cli_args|-m|examples_tag|--collect-only|
      Then pytest outcome must match lines:
        |collected 2 items / 1 deselected / 1 selected|

    Example:
      When run pytest
        |cli_args|-m|not feature_tag|--collect-only|
      Then pytest outcome must match lines:
        |collected 2 items / 2 deselected*|

    Example:
      When run pytest
        |cli_args|-m|not examples_tag|--collect-only|
      Then pytest outcome must match lines:
        |collected 2 items / 1 deselected / 1 selected|
