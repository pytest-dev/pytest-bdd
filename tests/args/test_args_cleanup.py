import re

import pytest
from pytest_bdd import scenario, given, then

test_function_argument_cleanup = scenario('args_steps.feature', 'Test function argument cleanup')


@pytest.fixture
def apples_quantity():
    return 5


@given(re.compile('I have (?P<apples_quantity>\d+) apples'))
def i_have_apples(apples_quantity):
    """I have 2 apples."""


@then('I should have 2 apples')
def i_should_have_2_apples(apples_quantity):
    assert int(apples_quantity) == 2


def test_apples_quantity(apples_quantity):
    assert apples_quantity == 5
