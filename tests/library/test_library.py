"""Test all the given steps are collected in the Library."""

import sys
from pytest_bdd import given
from pytest_bdd.library import Library


@given('I have local parent fixture')
def local_parent_fixture():
    pass


@given('I have a parent foo')
def foo():
    return 'parent'


def test_given_collected(request):
    """Test given steps are collected.

    Expects parent conftest and local fixtures.
    """

    module = sys.modules[test_given_collected.__module__]
    lib = Library(request, module)

    assert request.getfuncargvalue('foo') == 'parent'

    fixtures = lib.given.values()
    assert len(fixtures) == 4
    assert 'local_parent_fixture' in fixtures
    assert 'parent' in fixtures
    assert 'overridable' in fixtures
    assert 'foo' in fixtures
