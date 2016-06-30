"""Test tags."""
import pytest

from pytest_bdd import scenario, feature


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


def test_apply_tag_hook(testdir):
    testdir.makeconftest("""
        import pytest

        @pytest.hookimpl(tryfirst=True)
        def pytest_bdd_apply_tag(tag, function):
            if tag == 'todo':
                marker = pytest.mark.skipif(True, reason="Not implemented yet")
                marker(function)
                return True
            else:
                # Fall back to pytest-bdd's default behavior
                return None
    """)
    testdir.makefile('.feature', test="""
    Feature: Customizing tag handling

        @todo
        Scenario: Tags
            Given I have a bar

        @xfail
        Scenario: Tags 2
            Given I have a bar
    """)
    testdir.makepyfile("""
        from pytest_bdd import given, scenarios

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        scenarios('test.feature')
    """)
    result = testdir.runpytest('-rsx')
    result.stdout.fnmatch_lines(["SKIP *: Not implemented yet"])
    result.stdout.fnmatch_lines(["*= 1 skipped, 1 xpassed * =*"])


def test_tag_with_spaces(testdir):
    testdir.makeconftest("""
        import pytest

        @pytest.hookimpl(tryfirst=True)
        def pytest_bdd_apply_tag(tag, function):
            assert tag == 'test with spaces'
    """)
    testdir.makefile('.feature', test="""
    Feature: Tag with spaces

        @test with spaces
        Scenario: Tags
            Given I have a bar
    """)
    testdir.makepyfile("""
        from pytest_bdd import given, scenarios

        @given('I have a bar')
        def i_have_bar():
            return 'bar'

        scenarios('test.feature')
    """)
    result = testdir.runpytest_subprocess()
    result.stdout.fnmatch_lines(
        [
            "*= 1 passed * =*",
        ],
    )


@pytest.mark.parametrize('line, expected', [
    ('@foo @bar', {'foo', 'bar'}),
    ('@with spaces @bar', {'with spaces', 'bar'}),
    ('@double @double', {'double'}),
    ('    @indented', {'indented'}),
    (None, set()),
    ('foobar', set()),
    ('', set()),
])
def test_get_tags(line, expected):
    assert feature.get_tags(line) == expected
