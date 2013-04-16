"""Test givens declared in the parent conftest and plugin files.

Check the parent given steps are collected, override them locally.
"""

from pytest_bdd import given


@given('I have locally overriden fixture')
def overridable():
    return 'local'


@given('I have locally overriden parent fixture')
def parent():
    return 'local'


def test_override(request, overridable):
    """Test locally overriden fixture."""

    # Test the fixture is also collected by the text name
    assert request.getfuncargvalue('I have locally overriden fixture')(request) == 'local'

    # 'I have the overriden fixture' stands for overridable and is overriden locally
    assert request.getfuncargvalue('I have the overriden fixture')(request) == 'local'

    assert overridable == 'local'


def test_parent(parent):
    """Test locally overriden parent fixture."""
    assert parent == 'local'
