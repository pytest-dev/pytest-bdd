"""Pytest plugin entry point. Used for any fixtures needed."""

import os.path  # pragma: no cover

import pytest  # pragma: no cover


@pytest.fixture  # pragma: no cover
def pytestbdd_feature_base_dir(request):
    return os.path.dirname(request.module.__file__)
