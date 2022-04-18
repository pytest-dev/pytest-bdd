"""Test feature background."""

import textwrap

FEATURE = '''\
Feature: Some rules
    """
    Feature description
    """

  Background:
    """
    Background description
    """
    Given fb
      """
      Step description
      """

  Rule: A
    The rule A description

    Background:
      Given ab

    Example: Example A
      Given a

  Rule: B
    The rule B description

    Example: Example B
      Given b

  Rule: C
    The rule C description

    Example: Example CA
      Given c

    Rule: CB
        Example: CBA
          Given caa

        Example: CBB
          Given cab

        Example: CBC
          Given ca<key>

          Examples:
          | key |
          |  c  |
          |  d  |
          |  e  |
'''

STEPS = r"""\
from pytest_bdd import given



@given("{}")
def step():
    pass

"""


def test_background_basic(testdir):
    """Test feature background."""
    testdir.makefile(".feature", rule=textwrap.dedent(FEATURE))

    testdir.makeconftest(textwrap.dedent(STEPS))

    testdir.makepyfile(
        """\
        from pytest_bdd import scenarios

        scenarios("rule.feature")

        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=14)
