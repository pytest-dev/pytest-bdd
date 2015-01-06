"""Step arguments test configuration."""
import pytest


@pytest.fixture
def values():
    """List to ensure that steps are executed."""
    return [1, 2, 1, 0, 999999]
