"""Test tags."""
from pytest_bdd import scenario


def test_tags(request):
    """Test tags for the scenario and the feature."""
    @scenario(
        'tags.feature',
        'Tags'
    )
    def test():
        pass

    assert test.__scenario__.tags == set(['scenario_tag_1', 'scenario_tag_2'])
    assert test.__scenario__.feature.tags == set(['feature_tag_1', 'feature_tag_2'])

    assert getattr(test, 'scenario_tag_1')
    assert getattr(test, 'scenario_tag_2')

    assert getattr(test, 'feature_tag_1')
    assert getattr(test, 'feature_tag_2')

    test(request)


def test_tags_selector(testdir):
    """Test tests selection by tags."""
    testdir.makefile('.feature', test="""
    @feature_tag_1 @feature_tag_2
    Feature: Tags

    @scenario_tag_01 @scenario_tag_02
    Scenario: Tags
        Given I have a bar

    @scenario_tag_10 @scenario_tag_20
    Scenario: Tags 2
        Given I have a bar

    """)
    testdir.makepyfile("""
        import pytest
        from pytest_bdd import given, scenarios

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        scenarios('test.feature')
    """)
    result = testdir.runpytest('-k', 'scenario_tag_10 and not scenario_tag_01', '-vv').parseoutcomes()
    assert result['passed'] == 1
    assert result['deselected'] == 1

    result = testdir.runpytest('-k', 'scenario_tag_01 and not scenario_tag_10', '-vv').parseoutcomes()
    assert result['passed'] == 1
    assert result['deselected'] == 1

    result = testdir.runpytest('-k', 'feature_tag_1', '-vv').parseoutcomes()
    assert result['passed'] == 2

    result = testdir.runpytest('-k', 'feature_tag_10', '-vv').parseoutcomes()
    assert result['deselected'] == 2


def test_tags_after_background_issue_160(testdir):
    """Make sure using a tag after background works."""
    testdir.makefile('.feature', test="""
    Feature: Tags after background

        Background:
            Given I have a bar

        @tag
        Scenario: Tags
            Given I have a baz

        Scenario: Tags 2
            Given I have a baz
    """)
    testdir.makepyfile("""
        import pytest
        from pytest_bdd import given, scenarios

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        @given('I have a baz')
        def i_have_baz():
            return 'baz'

        scenarios('test.feature')
    """)
    result = testdir.runpytest('-m', 'tag', '-vv').parseoutcomes()
    assert result['passed'] == 1
    assert result['deselected'] == 1
