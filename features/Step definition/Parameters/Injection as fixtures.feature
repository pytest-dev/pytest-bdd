Feature: Step definitions parameters injection as fixtures
  Step arguments are injected into step context and could be used as normal
  fixtures with the names equal to the names of the arguments by default.

  Step's argument are accessible as a fixture in other step function just
  by mentioning it as an argument

  If the name of the step argument clashes with existing fixture,
  it will be overridden by step's argument value.
  Value for some fixture deeply inside of the fixture tree could be set/override
  in a ad-hoc way by just choosing the proper name for the step argument.

  Scenario: Step parameters are injected as fixtures by default
    Given File "conftest.py" with content:
      """python
      from re import compile as parse
      from pytest_bdd import given, then

      @given("I have a pickle", param_defaults=dict(freshness='salted'))
      @given(
        parse(r"I have a ((?P<freshness>\w+)\s)?cucumber"),
        param_defaults=dict(freshness='fresh')
      )
      def i_have_cucumber(freshness):
          ...

      @then("Taste of cucumber is salt")
      def i_check_salted_cucumber(freshness):
          assert freshness=='salted'
      """
    Given File "Freshness.feature" with content:
      """gherkin
      Feature:
        Scenario:
          Given I have a salted cucumber
          Then Taste of cucumber is salt
      """
    Given File "test_freshness.py" with content:
      """python
      from enum import Enum
      from pytest import fixture
      from pytest_bdd import scenario
      class Freshness(Enum):
        FRESH = 'fresh'
        ROTTEN = 'rotten'
        SALTED = 'salted'

      @fixture
      def oracle_freshness():
        return Freshness.SALTED

      @scenario("Freshness.feature")
      def test_passing_feature(request, oracle_freshness):
        assert Freshness(request.getfixturevalue('freshness'))==oracle_freshness

      @scenario("Freshness.feature")
      def test_another_passing_feature(freshness, oracle_freshness):
        assert Freshness(freshness)==oracle_freshness
      """
    When run pytest
      |cli_args|--disable-feature-autoload|
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     2|

  Scenario: Step parameters injection as fixtures could be disabled
    Given File "conftest.py" with content:
      """python
      from re import compile as parse
      from pytest_bdd import given, then

      @given(
        "I have a pickle",
        param_defaults=dict(freshness='salted'),
        params_fixtures_mapping={...:None},
        target_fixtures=['cuke_taste']
      )
      @given(
        parse(r"I have a ((?P<freshness>\w+)\s)?cucumber"),
        param_defaults=dict(freshness='fresh'),
        params_fixtures_mapping=False,
        target_fixture='cuke_taste'
      )
      def i_have_cucumber(freshness):
          assert freshness is not None
          yield freshness

      @then("Taste of cucumber is salt")
      def i_check_salted_cucumber(cuke_taste):
          assert cuke_taste=='salted'
      """
    Given File "Freshness.feature" with content:
      """gherkin
      Feature:
        Scenario:
          Given I have a pickle
          Then Taste of cucumber is salt
      """
    Given File "test_freshness.py" with content:
      """python
      import pytest
      from pytest_bdd import scenario
      from pytest_bdd.compatibility.pytest import FixtureLookupError
      @scenario("Freshness.feature")
      def test_passing_feature(request, cuke_taste):
        assert cuke_taste == 'salted'
        with pytest.raises(FixtureLookupError):
          request.getfixturevalue('freshness')
      """
    When run pytest
      |cli_args|--disable-feature-autoload|
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|

  Scenario: Step parameters renaming on injection as fixtures
    Given File "conftest.py" with content:
      """python
      from re import compile as parse
      from pytest_bdd import given, then

      @given(
        "I have a pickle",
        param_defaults=dict(freshness='salted'),
        params_fixtures_mapping={"freshness":"cuke_taste"}
      )
      @given(
        parse(r"I have a ((?P<freshness>\w+)\s)?cucumber"),
        param_defaults=dict(freshness='fresh'),
        params_fixtures_mapping={"freshness":"cuke_taste"}
      )
      def i_have_cucumber(cuke_taste, freshness):
          assert cuke_taste is not None
          assert freshness == cuke_taste
          yield cuke_taste

      @then("Taste of cucumber is salt")
      def i_check_salted_cucumber(cuke_taste):
          assert cuke_taste=='salted'
      """
    Given File "Freshness.feature" with content:
      """gherkin
      Feature:
        Scenario:
          Given I have a pickle
          Then Taste of cucumber is salt
      """
    Given File "test_freshness.py" with content:
      """python
      import pytest
      from pytest_bdd import scenario
      from pytest_bdd.compatibility.pytest import FixtureLookupError

      @scenario("Freshness.feature")
      def test_passing_feature(request, cuke_taste):
        assert cuke_taste == 'salted'
        with pytest.raises(FixtureLookupError):
          request.getfixturevalue('freshness')
      """
    When run pytest
      |cli_args|--disable-feature-autoload|
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|

  Scenario: Only allowed step parameters injection as fixtures
    Given File "conftest.py" with content:
      """python
      from pytest_bdd import given

      @given(
        "I have an old pickle",
        param_defaults=dict(freshness='salted', age='old'),
        params_fixtures_mapping={"freshness"}
      )
      def i_have_cucumber(age, freshness):
          assert age == 'old'
          assert freshness == 'salted'
      """
    Given File "Freshness.feature" with content:
      """gherkin
      Feature:
        Scenario:
          Given I have an old pickle
      """
    Given File "test_freshness.py" with content:
      """python
      import pytest
      from pytest_bdd import scenario
      from pytest_bdd.compatibility.pytest import FixtureLookupError

      @scenario("Freshness.feature")
      def test_passing_feature(request, freshness):
        assert freshness == 'salted'
        with pytest.raises(FixtureLookupError):
          request.getfixturevalue('age')
      """
    When run pytest
      |cli_args|--disable-feature-autoload|
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
