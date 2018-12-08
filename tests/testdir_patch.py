"""Tests that are testing config values need to be run using subprocess
to guarantee test separation and avoid messing with pytest internal state.
Pytest bug: https://github.com/pytest-dev/pytest/issues/4495

TODO: Remove this patch once above bug is fixed
"""
import pytest
from _pytest.pytester import Testdir


class PatchedTestdir(Testdir):

    def makeini(self, source):
        self._runpytest_method = self.runpytest_subprocess
        return self.makefile(".ini", tox=source)


@pytest.fixture
def testdir(request, tmpdir_factory):
    return PatchedTestdir(request, tmpdir_factory)
