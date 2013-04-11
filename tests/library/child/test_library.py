"""Test all the given steps are collected in the Library."""

from pytest_bdd import given
from pytest_bdd.library import Library


@given('I have local child fixture')
def local_child_fixture():
    pass


@given('I have child foo')
def foo():
    return 'child'


def test_given_collected(request):
    """Test given steps are collected.

    Expects parent conftest, local conftest and local fixtures.
    """
    lib = Library(request)

    assert request.getfuncargvalue('foo') == 'child'

    fixtures = lib.given.values()
    assert len(fixtures) == 5
    assert 'root' in fixtures
    assert 'local_child_fixture' in fixtures
    assert 'parent' in fixtures
    assert 'overridable' in fixtures
    assert 'foo' in fixtures
