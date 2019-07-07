"""Test scenario decorator."""
import pytest
import re

import six

from pytest_bdd import (
    scenario,
    given,
    then,
    parsers,
    exceptions,
)


def test_scenario_not_found(request):
    """Test the situation when scenario is not found."""
    with pytest.raises(exceptions.ScenarioNotFound) as exc_info:
        scenario(
            'not_found.feature',
            'NOT FOUND'
        )
    assert six.text_type(exc_info.value).startswith(
        'Scenario "NOT FOUND" in feature "[Empty]" in {feature_path}'
        .format(feature_path=request.fspath.join('..', 'not_found.feature')))


@given('comments should be at the start of words')
def comments():
    """Comments."""
    pass


@then(parsers.parse('this is not {acomment}'))
def a_comment(acomment):
    """A comment."""
    assert re.search('a.*comment', acomment)


def test_scenario_comments(request):
    """Test comments inside scenario."""
    @scenario(
        'comments.feature',
        'Comments'
    )
    def test():
        pass

    @scenario(
        'comments.feature',
        'Strings that are not comments'
    )
    def test2():
        pass

    test(request)
    test2(request)


def test_scenario_not_decorator(testdir):
    """Test scenario function is used not as decorator."""
    testdir.makefile('.feature', foo="""
        Scenario: Foo
            Given I have a bar
        """)
    testdir.makepyfile("""
        from pytest_bdd import scenario
        
        test_foo = scenario('foo.feature', 'Foo')
        """)

    result = testdir.runpytest()

    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines("*ScenarioIsDecoratorOnly: scenario function can only be used as a decorator*")
