# This is a comment
Feature: User login

  As a registered user
  I want to be able to log in
  So that I can access my account

  Background:
    # Background steps run before each scenario
    Given the login page is open

    # Scenario within the rule
  Scenario: Successful login with valid credentials
    Given the user enters a valid username
    And the user enters a valid password
    When the user clicks the login button
    Then the user should see the dashboard

  Scenario Outline: Unsuccessful login with invalid credentials
    Given the user enters "<username>" as username
    And the user enters "<password>" as password
    When the user clicks the login button
    Then the user should see an error message "<error_message>"

      # Examples table provides data for the scenario outline
    Examples:
      | username    | password  | error_message                |
      | invalidUser | wrongPass | Invalid username or password |
      | user123     | incorrect | Invalid username or password |

  Scenario: Login with empty username
    Given the user enters an empty username
    And the user enters a valid password
    When the user clicks the login button
    Then the user should see an error message "Username cannot be empty"

  Scenario: Login with empty password
    Given the user enters a valid username
    And the user enters an empty password
    When the user clicks the login button
    Then the user should see an error message "Password cannot be empty"

  Scenario: Login with SQL injection attempt
    Given the user enters "admin' OR '1'='1" as username
    And the user enters "password" as password
    When the user clicks the login button
    Then the user should see an error message "Invalid username or password"

  @login @critical
  Scenario: Login button disabled for empty fields
    Given the user has not entered any username or password
    Then the login button should be disabled

  # Tags can be used to categorize scenarios
  @smoke
  Scenario: Login page loads correctly
    Given the login page is loaded
    Then the login form should be visible

  # Using Data Tables for more complex data
  Scenario: Login with multiple sets of credentials
    Given the following users are registered:
      | username | password |
      | user1    | pass1    |
      | user2    | pass2    |
      | user3    | pass3    |
    When the user tries to log in with the following credentials:
      | username | password  |
      | user1    | pass1     |
      | user2    | wrongPass |
    Then the login attempts should result in:
      | username | result  |
      | user1    | success |
      | user2    | failure |

  # Using Doc Strings for multi-line text
  Scenario: Check login error message with detailed explanation
    Given the user enters invalid credentials
    When the user clicks the login button
    Then the user should see the following error message:
      """
      Your login attempt was unsuccessful.
      Please check your username and password and try again.
      If the problem persists, contact support.
      """

  @some-tag
  Rule: a sale cannot happen if there is no stock
  # Unhappy path
  Example: No chocolates left
    Given the customer has 100 cents
    And there are no chocolate bars in stock
    When the customer tries to buy a 1 cent chocolate bar
    Then the sale should not happen

  Rule: A sale cannot happen if the customer does not have enough money
    # Unhappy path
    Example: Not enough money
      Given the customer has 100 cents
      And there are chocolate bars in stock
      When the customer tries to buy a 125 cent chocolate bar
      Then the sale should not happen

    # Happy path
    Example: Enough money
      Given the customer has 100 cents
      And there are chocolate bars in stock
      When the customer tries to buy a 75 cent chocolate bar
      Then the sale should happen
