import pytest

from pytest_bdd import scenario, given, when, then
from pytest_bdd.scenario import ScenarioNotFound


@pytest.fixture
def pytestbdd_feature_file():
    return "no_feature_name.feature"


def test_scenario_not_found(request):
    """Test the situation when scenario is not found."""
    test_not_found = scenario(
        'not_found.feature',
        'NOT FOUND'
    )

    with pytest.raises(ScenarioNotFound):
        test_not_found(request)


def test_scenario_not_found_feature_name_not_specified(request):
    """Test the situation where scenario is not found and feature filename is not given."""
    test_not_found_feature_not_specified = scenario('NOT FOUND')

    with pytest.raises(ScenarioNotFound):
        test_not_found_feature_not_specified(request)


def test_scenario_specified_name_in_function_call(request):
    """Test the situation where the feature filename is specified in the function call."""
    test_specified_name_in_function_call = scenario(
        'not_found.feature',
        'Some scenario'
    )

    test_specified_name_in_function_call(request)


def test_scenario_specified_name_in_decorator_call(request):
    """Test the situation where the feature filename is specified in the decorator call."""
    @scenario('not_found.feature', 'Some scenario')
    def test_specified_name_in_decorator_call():
        """Decorator will do all the work for us."""

    test_specified_name_in_decorator_call(request)


def test_scenario_name_not_specified_function_call(request):
    """Test the situation where the scenario is called as a function but without scenario file."""
    test_name_not_specified_in_function_call = scenario('No feature name scenario')

    test_name_not_specified_in_function_call(request)


def test_scenario_name_not_specified_decorator_call(request):
    """Test the situation where the scenario is called as a decorator but without scenario file."""
    @scenario('No feature name scenario')
    def test_name_not_specified_in_decorator_call():
        """Decorator will do all the work for us."""

    test_name_not_specified_in_decorator_call(request)


@given('1')
@when('2')
@then('3')
def no_checks_at_all():
    pass
