import re
import pytest
from pytest_bdd import scenario, given, when, then
from pytest_bdd.scenario import GivenAlreadyUsed


test_steps = scenario(
    'args_steps.feature',
    'Every step takes a parameter with the same name',
)


@pytest.fixture
def values():
    return ['1', '2', '1', '0', '999999']


@given(re.compile(r'I have (?P<euro>\d+) Euro'))
def i_have(euro, values):
    assert euro == values.pop(0)


@when(re.compile(r'I pay (?P<euro>\d+) Euro'))
def i_pay(euro, values, request):
    assert euro == values.pop(0)


@then(re.compile(r'I should have (?P<euro>\d+) Euro'))
def i_should_have(euro, values):
    assert euro == values.pop(0)


def test_multiple_given(request):
    """Using the same given fixture raises an error."""
    test = scenario(
        'args_steps.feature',
        'Using the same given fixture raises an error',
    )
    with pytest.raises(GivenAlreadyUsed):
        test(request)
