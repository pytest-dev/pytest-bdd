"""Test descriptions."""
from pytest_bdd import scenario


def test_description(request):
    """Test description for the feature."""
    @scenario(
        'description.feature',
        'Description'
    )
    def test():
        pass

    assert test.__scenario__.feature.description == """In order to achieve something
I want something
Because it will be cool


Some description goes here."""
    assert test.__scenario__.description == """Also, the scenario can have a description.

It goes here between the scenario name
and the first step."""

    test(request)
