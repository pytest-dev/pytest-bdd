Feature: Step definitions parameters conversion
  There is possibility to pass argument converters which may be useful
  if you need to postprocess step arguments after the parser.

  Background:
    Given File "Example.feature" with content:
      """gherkin
      Feature:
        Scenario:
          Given I have a cucumber
      """

  Scenario: for non-anonymous groups
    Given File "conftest.py" with content:
      """python
      from enum import Enum
      from pytest_bdd import given
      from re import compile as parse

      class Item(Enum):
        CUCUMBER = 'cucumber'

      @given(parse(r"I have a (?P<item>\w+)"), converters=dict(item=Item))
      def i_have_item(item):
          assert item == Item.CUCUMBER
      """
    When run pytest
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|

  Rule: for anonymous groups
    Step definitions parameters could not have a name, so
    we have to name them before conversion

    Scenario:
      Given File "conftest.py" with content:
        """python
        from enum import Enum
        from pytest_bdd import given
        from re import compile as parse

        class Item(Enum):
          CUCUMBER = 'cucumber'

        @given(
          parse(r"I have a (\w+)"),
          anonymous_group_names=('item',),
          converters=dict(item=Item)
        )
        def i_have_item(item):
            assert item == Item.CUCUMBER
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|

    Scenario:
      Given File "conftest.py" with content:
        """python
        from enum import Enum
        from pytest_bdd import given
        from functools import partial
        from cucumber_expressions.expression import CucumberExpression
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

        parse = partial(
          CucumberExpression,
          parameter_type_registry = ParameterTypeRegistry()
        )

        class Item(Enum):
          CUCUMBER = 'cucumber'

        @given(
          parse(r"I have a {word}"),
          anonymous_group_names=('item',),
          converters=dict(item=Item)
        )
        def i_have_item(item):
            assert item == Item.CUCUMBER
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|
