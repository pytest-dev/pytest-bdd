"""Test givens declared in the parent conftest and plugin files.

Check the parent givens are collected and overriden in the local conftest.
"""


def test_parent(parent, overridable):
    """Test parent given is collected.

    Both fixtures come from the parent conftest.
    """
    assert parent == 'parent'
    assert overridable == 'parent'
