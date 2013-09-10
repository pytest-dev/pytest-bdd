import pytest

from pytest_bdd.scenario import NotEnoughScenarioParams

from pytest_bdd import given, when, then, scenario

PYTESTBDD_FEATURE_FILE = 'parametrized.feature'


@pytest.mark.parametrize(
    ['start', 'eat', 'left'],
    [(12, 5, 7)])
@scenario(
    'Parametrized given, when, thens',
)
def test_parametrized(request, start, eat, left):
    """Test parametrized scenario."""


def test_parametrized_wrongly(request):
    """Test parametrized scenario when the test function lacks parameters."""
    @scenario(
        'parametrized.feature',
        'Parametrized given, when, thens',
    )
    def wrongly_parametrized(request):
        pass

    with pytest.raises(NotEnoughScenarioParams) as exc:
        wrongly_parametrized(request)

        assert exc.value.args == (
            """Scenario "Parametrized given, when, thens" in the feature "parametrized.feature" was not able to """
            """resolve all declared parameters. """
            """Should resolve params: [\'eat\', \'left\', \'start\'], but resolved only: []."""
        )


@given('there are <start> cucumbers')
def start_cucumbers(start):
    return dict(start=start)


@when('I eat <eat> cucumbers')
def eat_cucumbers(start_cucumbers, start, eat):
    start_cucumbers['eat'] = eat


@then('I should have <left> cucumbers')
def should_have_left_cucumbers(start_cucumbers, start, eat, left):
    assert start - eat == left
    assert start_cucumbers['start'] == start
    assert start_cucumbers['eat'] == eat
