"""Test wrong feature syntax."""

from pytest_bdd import scenarios


def test_scenarios():
    """Test getting all scenarios from feature file."""

    ft = scenarios('steps.feature')
    assert ft.scenarios
    assert 'test_When step can be the first' in globals()
