"""Test descriptions."""
from pytest_bdd import scenario


test_file_contents = """
import pytest
from pytest_bdd import given, scenario

def test_descriptions(request):
    @scenario(
        "descriptions.feature",
        "Description",
    )
    def test():
        pass

    test(request)

@given("I have a bar")
def nothing():
    pass

"""

with open("./tests/feature/description.feature") as f:
    feature_file_contents = f.read()


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
    assert (
        test.__scenario__.description
        == """Also, the scenario can have a description.

It goes here between the scenario name
and the first step."""
    )

    test(request)


def test_scenarios_are_created_when_they_have_scenario_descriptions(testdir):
    testdir.makepyfile(test_descriptions=test_file_contents)
    testdir.makefile(".feature", descriptions=feature_file_contents)

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
