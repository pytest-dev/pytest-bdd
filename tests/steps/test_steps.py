"""Test when and then steps are callables."""

import pytest
from pytest_bdd import given, when, then
from pytest_bdd.steps import get_step_fixture_name, WHEN, THEN


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
    do_stuff_ = request.getfuncargvalue(get_step_fixture_name('I do stuff', WHEN))
    assert callable(do_stuff_)

    check_stuff_ = request.getfuncargvalue(get_step_fixture_name('I check stuff', THEN))
    assert callable(check_stuff_)


@pytest.mark.parametrize(
    ('step', 'keyword'), [
        (given, 'Given'),
        (when, 'When'),
        (then, 'Then')])
def test_preserve_decorator(step, keyword):
    """Check that we preserve original function attributes after decorating it."""
    @step(keyword)
    def func():
        """Doc string."""

    assert globals()[get_step_fixture_name(keyword, step.__name__)].__doc__ == 'Doc string.'
