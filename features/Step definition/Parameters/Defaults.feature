Feature: Step definitions parameters could have default values

  Scenario:
    Given File "Example.feature" with content:
      """gherkin
      Feature:
        Scenario:
          Given I have a cucumber
          Given I have a rotten cucumber
          Given I have a fresh cucumber
          Given I have a pickle
      """
    Given File "conftest.py" with content:
      """python
      from enum import Enum
      from re import compile as parse
      from pytest import fixture
      from pytest_bdd import given

      class Freshness(Enum):
        FRESH = 'fresh'
        ROTTEN = 'rotten'
        SALTED = 'salted'

      @fixture
      def oracle_freshness():
        return [Freshness.FRESH, Freshness.ROTTEN, Freshness.FRESH, Freshness.SALTED]

      @given("I have a pickle", param_defaults=dict(freshness=Freshness.SALTED))
      @given(
        parse(r"I have a ((?P<freshness>\w+)\s)?cucumber"),
        converters=dict(freshness=Freshness),
        param_defaults=dict(freshness=Freshness.FRESH)
      )
      def i_have_cucumber(freshness, oracle_freshness):
          assert freshness == oracle_freshness.pop(0)
      """
    When run pytest
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
