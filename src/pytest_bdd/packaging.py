from functools import lru_cache
from operator import eq
from typing import Any, Callable

from packaging.utils import Version

from pytest_bdd.compatibility.importlib.metadata import version


def get_distribution_version(distribution_name: str) -> Version:
    return Version(version(distribution_name))


def parse_version(version: str) -> Version:
    return Version(version)


@lru_cache
def compare_distribution_version(
    distribution_name: str, version: str, operator: Callable[[Any, Any], bool] = eq
) -> bool:
    return operator(get_distribution_version(distribution_name), parse_version(version))
