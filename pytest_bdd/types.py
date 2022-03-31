"""Common type definitions."""
from __future__ import annotations

from typing import TYPE_CHECKING

from _pytest.fixtures import FixtureRequest

from pytest_bdd.parser import ScenarioTemplate

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any

    from _pytest.nodes import Item as BaseItem
    from _pytest.reports import TestReport as BaseTestReport

    from pytest_bdd.reporting import ScenarioReport

    class TestReport(BaseTestReport):  # type: ignore[misc]
        scenario: dict[str, Any]
        item: dict[str, str]

    class TestFunc(type(lambda: ())):  # type: ignore[misc]
        __scenario__: ScenarioTemplate

    class Item(BaseItem):
        __scenario_report__: ScenarioReport
        obj: TestFunc
        _request: FixtureRequest
