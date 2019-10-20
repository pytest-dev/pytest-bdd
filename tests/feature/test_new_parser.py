import gherkin.parser

from pytest_bdd.feature import Feature, FeatureOld


def test_tags_after_background_issue_160(testdir):
    from pytest_bdd.feature import Feature

    """Make sure using a tag after background works."""

    f = testdir.makefile(
        ".feature",
        test="""
    Feature: Tags after background
        
        In order to achieve something
        I want something
        Because it will be cool
    
    
        Some description goes here.

        Background:
            Given I have a bar

        @tag
        Scenario: Tags
            Given I have a baz
            And I have a bar

        Scenario: Tags 2
            Given I have a baz
    """,
    )
    gherkin_feature = gherkin.parser.Parser().parse(str(f))
    this_feature = FeatureOld.get_feature(base_path=str(f.dirname), filename=str(f))
    new_feature = Feature(str(f.dirname), filename=str(f))
    gherkin_feature == this_feature
    testdir.makepyfile(
        """
        import pytest
        from pytest_bdd import given, scenarios

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        @given('I have a baz')
        def i_have_baz():
            return 'baz'

        scenarios('test.feature')
    """
    )
    result = testdir.runpytest("-m", "tag", "-vv").parseoutcomes()
    assert result["passed"] == 1
    assert result["deselected"] == 1
