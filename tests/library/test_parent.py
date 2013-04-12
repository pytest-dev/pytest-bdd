"""Test givens declared in the parent conftest and plugin files.

Check the parent givens are collected and overriden in the local conftest.
"""


def test_parent(parent, overridable):
    """Test parent given is collected.

    Both fixtures come from the parent conftest.
    """
    assert parent == 'parent'
    assert overridable == 'parent'


def test_global_when_step(request):
    """Test when step defined in the parent conftest."""
    request.getfuncargvalue('I use a when step from the parent conftest')
