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

    assert test.__scenario__.tags == set(['@scenario-tag-1', '@scenario-tag-2'])
    assert test.__scenario__.feature.tags == set(['@feature-tag-1', '@feature-tag-2'])

    assert getattr(test, '@scenario-tag-1')
    assert getattr(test, '@scenario-tag-2')

    assert getattr(test, '@feature-tag-1')
    assert getattr(test, '@feature-tag-2')

    test(request)
