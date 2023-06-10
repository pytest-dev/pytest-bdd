from __future__ import annotations

import sys
from functools import lru_cache
from operator import eq
from typing import Any, Callable

from packaging.utils import Version

if sys.version_info >= (3, 10):
    from importlib.metadata import version
else:
    from importlib_metadata import version


def get_distribution_version(distribution_name: str) -> Version:
    return Version(version(distribution_name))


def parse_version(version: str) -> Version:
    return Version(version)


@lru_cache()
def compare_distribution_version(
    distribution_name: str, version: str, operator: Callable[[Any, Any], bool] = eq
) -> bool:
    return operator(get_distribution_version(distribution_name), parse_version(version))
