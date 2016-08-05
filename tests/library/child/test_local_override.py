"""Test givens declared in the parent conftest and plugin files.

Check the parent given steps are collected, override them locally.
"""

from pytest_bdd import given
from pytest_bdd.steps import get_step_fixture_name, GIVEN
from pytest_bdd.utils import get_fixture_value


@given('I have locally overriden fixture')
def overridable():
    return 'local'


@given('I have locally overriden parent fixture')
def parent():
    return 'local'


def test_override(request, overridable):
    """Test locally overriden fixture."""

    # Test the fixture is also collected by the text name
    fixture = get_fixture_value(request, get_step_fixture_name('I have locally overriden fixture', GIVEN))
    assert fixture(request) == 'local'

    # 'I have the overriden fixture' stands for overridable and is overriden locally
    fixture = get_fixture_value(request, get_step_fixture_name('I have the overriden fixture', GIVEN))
    assert fixture(request) == 'local'

    assert overridable == 'local'


def test_parent(parent):
    """Test locally overriden parent fixture."""
    assert parent == 'local'
