Feature: Step definitions parameters parsing by custom parser
  Scenario:
    Given File "Example.feature" with content:
      """gherkin
      Feature:
        Scenario:
          Given there are 10 cucumbers
      """
    Given File "conftest.py" with content:
      """python
      import re
      from pytest_bdd import given, parsers

      class Parser(parsers.StepParser):
          def __init__(self, name, *args,**kwargs):
              self.name = name
              self.regex = re.compile(
                re.sub("%(.+)%", r"(?P<\1>.+)", name),
                *args,
                **kwargs
              )

          def parse_arguments(self, request, name, **kwargs):
              __doc__ = "Parse step arguments"
              return self.regex.match(name).groupdict()

          @property
          def arguments(self):
              return [*self.regex.groupindex.keys()]

          def is_matching(self, request ,name):
              __doc__ = "Match given name with the step name."
              return bool(self.regex.match(name))

          def __str__(self):
            return self.name

      @given(
        Parser("there are %start% cucumbers"),
        target_fixture="start_cucumbers",
        converters=dict(start=int)
      )
      def start_cucumbers(start):
          assert start == 10
      """
    When run pytest
    Then pytest outcome must contain tests with statuses:
      |passed|
      |     1|
