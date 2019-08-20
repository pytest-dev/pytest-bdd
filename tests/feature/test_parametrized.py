import pytest

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


@pytest.mark.parametrize(
    'start', [12, 5]
)
@scenario(
    'parametrized.feature',
    'Parametrized given, then - single parameter name',
)
def test_parametrized_single_parameter_name(request, start):
    """Test parametrized scenario."""


@pytest.fixture(params=[1, 2])
def foo_bar(request):
    return 'bar' * request.param


@pytest.mark.parametrize(
    ['start', 'eat', 'left'],
    [(12, 5, 7)])
@scenario(
    'parametrized.feature',
    'Parametrized given, when, thens',
)
def test_parametrized_with_other_fixtures(request, start, eat, left, foo_bar):
    """Test parametrized scenario, but also with other parametrized fixtures."""


@given('there are <start> cucumbers')
def start_cucumbers(start):
    return dict(start=start)


@when('I eat <eat> cucumbers')
def eat_cucumbers(start_cucumbers, start, eat):
    start_cucumbers['eat'] = eat


@when('I do not eat any cucumber')
def do_not_eat_any_cucumber():
    pass


@then('I should have <left> cucumbers')
def should_have_left_cucumbers(start_cucumbers, start, eat, left):
    assert start - eat == left
    assert start_cucumbers['start'] == start
    assert start_cucumbers['eat'] == eat


@then('I still should have <start> cucumbers')
def still_should_have_start_cucumbers(start_cucumbers, start):
    assert start_cucumbers['start'] == start
