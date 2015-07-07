"""Test wrong feature syntax."""
import os.path
import re

import mock

import pytest

from pytest_bdd import scenario, scenarios, given, when, then
from pytest_bdd.feature import features
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
    ('feature', 'scenario_name'),
    [
        ('when_in_background.feature', 'When in background'),
        ('when_after_then.feature', 'When after then'),
        ('then_first.feature', 'Then first'),
        ('given_after_when.feature', 'Given after When'),
        ('given_after_then.feature', 'Given after Then'),
    ]
)
@pytest.mark.parametrize('strict_gherkin', [True, False])
@pytest.mark.parametrize('multiple', [True, False])
@mock.patch('pytest_bdd.fixtures.pytestbdd_strict_gherkin', autospec=True)
def test_wrong(mocked_strict_gherkin, request, feature, scenario_name, strict_gherkin, multiple):
    """Test wrong feature scenarios."""
    mocked_strict_gherkin.return_value = strict_gherkin

    def declare_scenario():
        if multiple:
            scenarios(feature)
        else:
            @scenario(feature, scenario_name)
            def test_scenario():
                pass

    if strict_gherkin:
        with pytest.raises(exceptions.FeatureError):
            declare_scenario()
        # TODO: assert the exception args from parameters
    else:
        declare_scenario()

    def clean_cache():
        features.clear()
    request.addfinalizer(clean_cache)


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


def test_verbose_output():
    """Test verbose output of failed feature scenario."""
    with pytest.raises(exceptions.FeatureError) as excinfo:
        scenario('when_after_then.feature', 'When after then')

    msg, line_number, line, file = excinfo.value.args

    assert line_number == 5
    assert line == 'When I do it again'
    assert file == os.path.join(os.path.dirname(__file__), 'when_after_then.feature')
    assert line in str(excinfo.value)


def test_multiple_features_single_file():
    """Test validation error when multiple features are placed in a single file."""
    with pytest.raises(exceptions.FeatureError) as excinfo:
        scenarios('wrong_multiple_features.feature')
    assert excinfo.value.args[0] == 'Multiple features are not allowed in a single feature file'
