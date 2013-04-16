"""Test when and then steps are callables."""

from pytest_bdd import when, then


@when('I do stuff')
def do_stuff():
    pass


@then('I check stuff')
def check_stuff():
    pass


def test_when_then(request):
    """Test when and then steps are callable functions.

    This test checks that when and then are not evaluated
    during fixture collection that might break the scenario.
    """
    do_stuff_ = request.getfuncargvalue('I do stuff')
    assert callable(do_stuff_)

    check_stuff_ = request.getfuncargvalue('I check stuff')
    assert callable(check_stuff_)
