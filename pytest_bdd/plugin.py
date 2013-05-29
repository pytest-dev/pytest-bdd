"""Pytest plugin entry point. Used for any fixtures needed."""

import os.path

import pytest


@pytest.fixture
def pytestbdd_feature_base_dir(request):
    return os.path.dirname(request.module.__file__)
