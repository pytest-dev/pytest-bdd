# Feature:
## Background:
* Given File "Passing.feature" with content:
    ```gherkin
    Feature: Passing feature
      Scenario: Passing scenario
        Given Passing step
    ```
* And File "conftest.py" with content:
    ```python
    from pytest_bdd import step

    @step('Passing step')
    def _():
      ...
    ```

## Scenario: NDJson(JSONL) could be produced on the feature run
    Output file could be fed into other @cucumber tools for more verbose report
    [Messages](https://github.com/cucumber/messages)

* When run pytest
    | cli_args   | --messages-ndjson | out.ndjson |
    |------------|-------------------|------------|
    | subprocess | true              |            |

* Then File "out.ndjson" has "15" lines
* Then Report "out.ndjson" parsable into messages

## Scenario: HTML report could be produced on the feature run
    Dummy reporter based on [@cucumber/html-formatter](https://github.com/cucumber/html-formatter)

* Given Install npm packages
    | packages | @cucumber/html-formatter |
    |----------|--------------------------|

* When run pytest
    | cli_args   | --cucumber-html | out.html |
    |------------|-----------------|----------|
    | subprocess | true            |          |

* Then File "out.html" is not empty
