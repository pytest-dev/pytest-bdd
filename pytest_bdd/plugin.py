import os.path

import pytest


@pytest.fixture
def pytestbdd_feature_path(request):
    return os.path.dirname(request.module.__file__)
