"""Test wrong feature syntax."""
import re

import pytest

from pytest_bdd import scenario, given, when, then
from pytest_bdd import exceptions


@given('something')
def given_something():
    pass


@when('something else')
def when_something_else():
    pass


@then('nevermind')
def then_nevermind():
    pass


@pytest.mark.parametrize(
    'scenario_name',
    [
        'When in Given',
        'When in Then',
        'Then in Given',
        'Given in When',
        'Given in Then',
        'Then in When',
    ]
)
def test_wrong_type_order(request, scenario_name):
    """Test wrong step type order."""
    @scenario('wrong_type_order.feature', scenario_name)
    def test_wrong_type_order(request):
        pass

    with pytest.raises(exceptions.StepDefinitionNotFoundError) as excinfo:
        test_wrong_type_order(request)
    assert re.match(r'Step definition is not found: (.+)', excinfo.value.args[0])
