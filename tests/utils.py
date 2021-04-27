import pytest
from packaging.utils import Version

PYTEST_VERSION = Version(pytest.__version__)
PYTEST_6 = PYTEST_VERSION >= Version("6")


if PYTEST_6:

    def assert_outcomes(
        result,
        passed=0,
        skipped=0,
        failed=0,
        errors=0,
        xpassed=0,
        xfailed=0,
    ):
        """Compatibility function for result.assert_outcomes"""
        return result.assert_outcomes(
            errors=errors, passed=passed, skipped=skipped, failed=failed, xpassed=xpassed, xfailed=xfailed
        )


else:

    def assert_outcomes(
        result,
        passed=0,
        skipped=0,
        failed=0,
        errors=0,
        xpassed=0,
        xfailed=0,
    ):
        """Compatibility function for result.assert_outcomes"""
        return result.assert_outcomes(
            error=errors,  # Pytest < 6 uses the singular form
            passed=passed,
            skipped=skipped,
            failed=failed,
            xpassed=xpassed,
            xfailed=xfailed,
        )
