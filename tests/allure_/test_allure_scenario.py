from pytest import mark

from pytest_bdd import scenario
from pytest_bdd.typing.allure import ALLURE_INSTALLED


@scenario("tests/allure_/features/scenario.feature", "Simple passed scenario")
@mark.skipif(not ALLURE_INSTALLED, reason="Allure is not installed")
def test_simple_passed_scenario():
    pass
