Feature: Step definitions parameters parsing
  Step parameters often enable the reuse of steps,
  which can reduce the amount of code required.
  This methodology allows for the same step
  to be used multiple times within a single scenario,
  but with different arguments.
  There are an multiple step parameter parsers available for your use.

  Rule: Step definitions parameters parsing
    Background:
      Given File "Parametrized.feature" with content:
        """gherkin
        Feature: StepHandler arguments
          Scenario: Every step takes a parameter with the same name
            Given I have a wallet
            Given I have 6 Euro
            When I lose 3 Euro
            And I pay 2 Euro
            Then I should have 1 Euro
            # In my dream...
            And I should have 999999 Euro
        """

    Scenario: Heuristic parser guesses a type and builds particular parser to be applied
      Tries to select right parser between string, cucumber_expression, cfparse and re.
      Any object that supports `__str__` interface and does not support parser interface
      will be wrapped with this parser

      Given File "conftest.py" with content:
        """python
        import pytest
        from pytest_bdd import given, when, then

        @pytest.fixture
        def values():
            return [6, 3, 2, 1, 999999]

        # string parser
        @given("I have a wallet", param_defaults={'wallet': 'wallet'})
        def i_have_wallet(wallet):
            assert wallet == 'wallet'

        # cucumber expressions parser
        @given("I have {int} Euro",
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_have(euro, values):
            assert euro == values.pop(0)

        # parse parser
        @when(
          "I pay {} Euro",
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_pay(euro, values):
            assert euro == values.pop(0)

        # cfparse parser
        @when("I lose {euro:d} Euro", converters=dict(euro=int))
        def i_lose(euro, values):
            assert euro == values.pop(0)

        # regular expression parser
        @then(
          r"I should have (\d+) Euro",
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|

    Scenario: by "parse"
      http://pypi.python.org/pypi/parse

      Provides a simple parser that replaces regular expressions for
      step parameters with a readable syntax like ``{param:Type}``.
      The syntax is inspired by the Python builtin ``string.format()``
      function.
      Step parameters must use the named fields syntax of pypi_parse_
      in step definitions. The named fields are extracted,
      optionally type converted and then used as step function arguments.
      Supports type conversions by using type converters passed via `extra_types`

      Given File "conftest.py" with content:
        """python
        import pytest
        from pytest_bdd import given, when, then
        from parse import Parser as parse

        @pytest.fixture
        def values():
            return [6, 3, 2, 1, 999999]

        @given(parse("I have a wallet"), param_defaults={'wallet': 'wallet'})
        def i_have_wallet(wallet):
            assert wallet == 'wallet'

        @given(parse("I have {euro:g} Euro"))
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(parse("I pay {euro:d} Euro"))
        def i_pay(euro, values):
            assert euro == values.pop(0)

        @when(
          parse("I lose {} Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_pay(euro, values):
            assert euro == values.pop(0)

        @then(
          parse(r"I should have {:d} Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|

    Scenario: by "cfparse"
      http://pypi.python.org/pypi/parse_type

      Provides an extended parser with "Cardinality Field" (CF) support.
      Automatically creates missing type converters for related cardinality
      as long as a type converter for cardinality=1 is provided.
      Supports parse expressions like:
      ``{values:Type+}`` (cardinality=1..N, many)
      ``{values:Type*}`` (cardinality=0..N, many0)
      ``{value:Type?}``  (cardinality=0..1, optional)
      Supports type conversions (as above).

      Given File "conftest.py" with content:
        """python
        import pytest
        from pytest_bdd import given, when, then
        from parse_type.cfparse import Parser as parse

        @pytest.fixture
        def values():
            return [6, 3, 2, 1, 999999]

        @given(parse("I have a wallet"), param_defaults={'wallet': 'wallet'})
        def i_have_wallet(wallet):
            assert wallet == 'wallet'

        @given(parse("I have {euro:Number} Euro", extra_types=dict(Number=int)))
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(parse("I pay {euro:d} Euro"))
        def i_pay(euro, values):
            assert euro == values.pop(0)

        @when(
          parse("I lose {} Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_pay(euro, values):
            assert euro == values.pop(0)

        @then(
          parse(r"I should have {:d} Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_should_have(euro, values):
            assert euro == values.pop(0)

        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|

    Scenario: by "cucumber-expressions"
      https://github.com/cucumber/cucumber-expressions
      Cucumber Expressions is an alternative to Regular Expressions
      with a more intuitive syntax.

      And File "conftest.py" with content:
        """python
        from functools import partial
        import pytest
        from pytest_bdd import given, when, then
        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
        from cucumber_expressions.expression import CucumberExpression

        parse = partial(
          CucumberExpression,
          parameter_type_registry = ParameterTypeRegistry()
        )

        @pytest.fixture
        def values():
            return [6, 3, 2, 1, 999999]

        @given(parse("I have a wallet"), param_defaults={'wallet': 'wallet'})
        def i_have_wallet(wallet):
            assert wallet == 'wallet'

        @given(
          parse("I have {int} Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(
          parse("I pay {} Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_pay(euro, values, request):
            assert euro == values.pop(0)

        @when(
          parse(r"I lose {int} Dollar/Euro(s)"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_lose(euro, values):
            assert euro == values.pop(0)

        @then(
          parse("I should have {int} Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|

    Scenario: by "cucumber-regular-expressions"
      https://github.com/cucumber/cucumber-expressions
      Cucumber Expressions is an alternative
    to Regular Expressions with a more intuitive syntax.

      And File "conftest.py" with content:
        """python
        import pytest
        from pytest_bdd import given, when, then
        from functools import partial

        from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
        from cucumber_expressions.regular_expression import (
          RegularExpression as CucumberRegularExpression
        )

        parse = partial(
          CucumberRegularExpression,
          parameter_type_registry = ParameterTypeRegistry()
        )

        @pytest.fixture
        def values():
            return [6, 3, 2, 1, 999999]

        @given(parse("I have a wallet"), param_defaults={'wallet': 'wallet'})
        def i_have_wallet(wallet):
            assert wallet == 'wallet'

        @given(
          parse(r"I have (\d+) Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_have(euro, values):
            assert euro == values.pop(0)

        @when(
          parse("I pay (.*) Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_pay(euro, values, request):
            assert euro == values.pop(0)

        @when(
          parse(r"I lose (.+) Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_lose(euro, values):
            assert euro == values.pop(0)

        @then(
          parse(r"I should have (\d+) Euro"),
          anonymous_group_names=('euro',),
          converters=dict(euro=int)
        )
        def i_should_have(euro, values):
            assert euro == values.pop(0)
        """
      When run pytest
      Then pytest outcome must contain tests with statuses:
        |passed|
        |     1|

    Scenario: by "regular-expressions"
    This uses full regular expressions to parse the clause text. You will
    need to use named groups "(?P<name>...)" to define the variables pulled
    from the text and passed to your "step()" function.
    Type conversion can only be done via "converters" step decorator
    argument (see example in according feature).

    Given File "conftest.py" with content:
      """python
      import pytest
      from pytest_bdd import given, when, then
      from re import compile as parse

      @pytest.fixture
      def values():
          return [6, 3, 2, 1, 999999]

      @given(parse("I have a wallet"), param_defaults={'wallet': 'wallet'})
      def i_have_wallet(wallet):
          assert wallet == 'wallet'

      @given(parse(r"I have (?P<euro>\d+) Euro"), converters=dict(euro=int))
      def i_have(euro, values):
          assert euro == values.pop(0)

      @when(
        parse(r"I pay (\d+) Euro"),
        anonymous_group_names=('euro',),
        converters=dict(euro=int)
      )
      def i_pay(euro, values):
          assert euro == values.pop(0)

      @when(parse(r"I lose (.+) Euro"),
        anonymous_group_names=('euro',),
        converters=dict(euro=int)
      )
      def i_lose(euro, values):
          assert euro == values.pop(0)

      @then(parse(r"I should have (?P<euro>\d+) Euro"), converters=dict(euro=int))
      def i_should_have(euro, values):
          assert euro == values.pop(0)
      """
    When run pytest
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
