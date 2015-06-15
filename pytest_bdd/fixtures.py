"""pytest-bdd built-in fixtures."""

import os.path

import pytest


@pytest.fixture
def pytestbdd_feature_base_dir(request):
    """Base feature directory."""
    return os.path.dirname(request.module.__file__)


@pytest.fixture
def pytestbdd_strict_gherkin():
    """Parse features to be strict gherkin."""
    return True
