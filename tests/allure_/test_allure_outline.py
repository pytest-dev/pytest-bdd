from pytest import mark

from pytest_bdd import scenario
from pytest_bdd.typing.allure import ALLURE_INSTALLED


@scenario("tests/allure_/features/outline.feature", "Scenario outline")
@mark.skipif(not ALLURE_INSTALLED, reason="Allure is not installed")
def test_scenario_outline():
    pass
