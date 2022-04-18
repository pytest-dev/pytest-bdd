"""Common type definitions."""
from __future__ import annotations

from typing import TYPE_CHECKING

from _pytest.fixtures import FixtureRequest

from pytest_bdd.feature import Feature
from pytest_bdd.pickle import Pickle

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any

    from _pytest.nodes import Item as BaseItem
    from _pytest.reports import TestReport as BaseTestReport

    from pytest_bdd.reporting import ScenarioReport

    class TestReport(BaseTestReport):  # type: ignore[misc]
        scenario: dict[str, Any]
        item: dict[str, str]

    class TestFunc(type(lambda: ())):  # type: ignore[misc]
        __pytest_bdd_pickle__: Pickle
        __pytest_bdd_feature__: Feature

    class Item(BaseItem):
        __pytest_bdd_scenario_report__: ScenarioReport
        obj: TestFunc
        _request: FixtureRequest
