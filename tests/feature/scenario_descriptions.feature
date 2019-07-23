Feature: Scenario Descriptions

  Just as this feature has a feature descriptions,
  which you are currently reading,
  users should be able to add a description for a scenario

  The scenarios in this feature file are skipped intentionally.
  This issue: https://github.com/pytest-dev/pytest-bdd/issues/311
  shows that scenario descriptions caused new tests to be created.
  Those tests didn't have the markers attached to them,
  so without the fix for that issue,
  those new, rogue tests would fail with StepDefinitionNotFoundError.

  If these scenarios' steps were implemented,
  then all of these new, rogue tests would execute and pass.

  @skip
  Scenario: A scenario with a description
    Here is a scenario description that is just one line

    Given something
    When I do something
    Then something happens

  @skip
  Scenario: A scenario with a multiline description
    Here is a scenario description.
    It can also have more lines.

    There can be line breaks too.
    You just can't start a line with a real step keyword,
    otherwise it will be treated as a step.

    Given something
    When I do something
    Then something happens
