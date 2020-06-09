"""Test descriptions."""

import textwrap

from pytest_bdd import given, scenario


@given("I have a bar")
def bar():
    return "bar"


def test_description(request, testdir):
    """Test description for the feature."""
    feature = testdir.makefile(
        ".feature",
        description=textwrap.dedent(
            """\
        Feature: Description

            In order to achieve something
            I want something
            Because it will be cool


            Some description goes here.

            Scenario: Description
                Given I have a bar
        """
        ),
    )

    @scenario(feature.strpath, "Description")
    def test_description(request):
        pass

    test_description(request)

    assert test_description.__scenario__.feature.description == textwrap.dedent(
        """\
        In order to achieve something
        I want something
        Because it will be cool


        Some description goes here."""
    )
