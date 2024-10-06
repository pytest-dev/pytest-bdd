Feature: Step definition could override or setup new fixture
  Dependency injection is not a panacea if you have complex structure of your test setup data.
  Sometimes there's a need such a given step which would imperatively change
  the fixture only for certain test (scenario), while for other tests
  it will stay untouched. To allow this, special parameter `target_fixture` exists in the decorator:

  Scenario: Single fixture injection
    Given File "conftest.py" with content:
      """python
      from pytest_bdd import given

      @given("I have an old pickle", param_defaults={"age": "old"}, target_fixture='pickle_age', params_fixtures_mapping=False)
      def i_have_cucumber(age):
          yield age
      """
    Given File "Freshness.feature" with content:
      """gherkin
      Feature:
        Scenario:
          Given I have an old pickle
      """
    Given File "test_freshness.py" with content:
      """python
      from pytest_bdd import scenario

      @scenario("Freshness.feature")
      def test_passing_feature(pickle_age, request):
        assert pickle_age == 'old'
        assert request.getfixturevalue('pickle_age') == pickle_age
      """
    When run pytest
      |cli_args|--disable-feature-autoload|
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
  Scenario: Multiple fixtures injection
    Given File "conftest.py" with content:
      """python
      from pytest_bdd import given

      @given("I have an old pickle", target_fixtures=['pickle_age', 'cucumber_kind'])
      def i_have_cucumber():
          yield ['old', 'pickle']
      """
    Given File "Freshness.feature" with content:
      """gherkin
      Feature:
        Scenario:
          Given I have an old pickle
      """
    Given File "test_freshness.py" with content:
      """python
      from pytest_bdd import scenario

      @scenario("Freshness.feature")
      def test_passing_feature(request, pickle_age, cucumber_kind):
        assert pickle_age == 'old'
        assert cucumber_kind == 'pickle'
        assert request.getfixturevalue('pickle_age') == pickle_age
        assert request.getfixturevalue('cucumber_kind') == cucumber_kind
      """
    When run pytest
      |cli_args|--disable-feature-autoload|
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
