"""Test descriptions."""
from pytest_bdd import scenario


def test_description(request):
    """Test description for the feature."""

    @scenario("description.feature", "Description")
    def test():
        pass

    assert (
        test.__scenario__.feature.description
        == """In order to achieve something
I want something
Because it will be cool


Some description goes here."""
    )

    test(request)
