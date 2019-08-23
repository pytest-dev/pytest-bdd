"""Test givens declared in the parent conftest and plugin files.

Check the parent givens are collected and overriden in the local conftest.
"""


def test_parent(parent):
    """Test parent given is collected."""
    assert parent == "parent"


def test_override(overridable):
    """Test the child conftest overriding the fixture."""
    assert overridable == "child"
