from pytest import mark

from pytest_bdd import scenario
from pytest_bdd.compatibility.allure import ALLURE_INSTALLED
from pytest_bdd.compatibility.pytest import PYTEST81


@scenario("testdata/allure_/outline.feature", "Scenario outline")
@mark.skipif(not ALLURE_INSTALLED, reason="Allure is not installed")
@mark.skipif(PYTEST81, reason="Allure uses deprecated APIs")
def test_scenario_outline():
    pass
