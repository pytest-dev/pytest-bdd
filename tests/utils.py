from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from packaging.utils import Version

if TYPE_CHECKING:
    from pytest_bdd.typing.pytest import RunResult

PYTEST_VERSION = Version(pytest.__version__)
PYTEST_6 = PYTEST_VERSION >= Version("6")


if PYTEST_6:

    def assert_outcomes(
        result: RunResult,
        passed: int = 0,
        skipped: int = 0,
        failed: int = 0,
        errors: int = 0,
        xpassed: int = 0,
        xfailed: int = 0,
    ) -> None:
        """Compatibility function for result.assert_outcomes"""
        result.assert_outcomes(
            errors=errors, passed=passed, skipped=skipped, failed=failed, xpassed=xpassed, xfailed=xfailed
        )

else:

    def assert_outcomes(
        result: RunResult,
        passed: int = 0,
        skipped: int = 0,
        failed: int = 0,
        errors: int = 0,
        xpassed: int = 0,
        xfailed: int = 0,
    ) -> None:
        """Compatibility function for result.assert_outcomes"""
        result.assert_outcomes(
            error=errors,  # Pytest < 6 uses the singular form
            passed=passed,
            skipped=skipped,
            failed=failed,
            xpassed=xpassed,
            xfailed=xfailed,
        )
