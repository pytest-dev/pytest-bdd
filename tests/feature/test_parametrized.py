import pytest

from pytest_bdd.steps import NotEnoughStepParams
from pytest_bdd.scenario import NotEnoughScenarioParams

from pytest_bdd import given, when, then, scenario


@pytest.mark.parametrize(
    ['start', 'eat', 'left'],
    [(12, 5, 7)])
@scenario(
    'parametrized.feature',
    'Parametrized given, when, thens',
)
def test_parametrized(request, start, eat, left):
    """Test parametrized scenario."""


def test_parametrized_given():
    """Test parametrized given."""
    with pytest.raises(NotEnoughStepParams) as exc:
        @given('there are <some> cucumbers')
        def some_cucumbers():
            return {}
    assert exc.value.args == (
        'Step "there are <some> cucumbers" doesn\'t have enough parameters declared.\n'
        'Should declare params: [\'some\'], but declared only: []',)


def test_parametrized_when():
    """Test parametrized when."""
    with pytest.raises(NotEnoughStepParams) as exc:
        @when('I eat <some> cucumbers')
        def some_cucumbers():
            return {}
    assert exc.value.args == (
        'Step "I eat <some> cucumbers" doesn\'t have enough parameters declared.\n'
        'Should declare params: [\'some\'], but declared only: []',)


def test_parametrized_then():
    """Test parametrized then."""
    with pytest.raises(NotEnoughStepParams) as exc:
        @when('I should have <some> cucumbers')
        def some_cucumbers():
            return {}
    assert exc.value.args == (
        'Step "I should have <some> cucumbers" doesn\'t have enough parameters declared.\n'
        'Should declare params: [\'some\'], but declared only: []',)


def test_parametrized_wrongly(request):
    """Test parametrized scenario when the test function lacks parameters."""
    @scenario(
        'parametrized.feature',
        'Parametrized given, when, thens',
    )
    def test_parametrized_wrongly(request):
        pass

    with pytest.raises(NotEnoughScenarioParams) as exc:
        test_parametrized_wrongly(request)

    assert exc.value.args == (
        'Scenario "Parametrized given, when, thens" in feature "parametrized.feature" doesn\'t have enough '
        'parameters declared.\nShould declare params: [\'start\', \'eat\', \'left\'], but declared only: []',
    )


@given('there are <start> cucumbers')
def start_cucumbers(start):
    return dict(start=start)


@when('I eat <eat> cucumbers')
def eat_cucumbers(start_cucumbers, start, eat):
    assert start_cucumbers['start'] == start


@then('I should have <left> cucumbers')
def should_have_left_cucumbers(start, eat, left):
    assert start - eat == left
