"""Common type definitions."""
from __future__ import annotations

from typing import TYPE_CHECKING

from _pytest.fixtures import FixtureRequest

if TYPE_CHECKING:  # pragma: no cover

    from _pytest.nodes import Item as BaseItem

    class Item(BaseItem):
        _request: FixtureRequest
