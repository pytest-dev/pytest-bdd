"""Test scenario decorator."""
import pytest
import re

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
    assert exc_info.value.args[0].startswith('Scenario "NOT FOUND" in feature "[Empty]" in {feature_path}'.format(
        feature_path=request.fspath.join('..', 'not_found.feature')))


@given('comments should be at the start of words')
def comments():
    pass


@then(parsers.parse('this is not {acomment}'))
def a_comment(acomment):
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
