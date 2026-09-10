"""Compat tests."""

from __future__ import annotations

from unittest import mock

from packaging.version import parse as parse_version

import pytest_bdd.compat as compat


def test_inject_fixture_uses_node_on_pytest_9_1_and_later(monkeypatch):
    """inject_fixture passes ``node=`` once pytest deprecates ``nodeid=``."""
    monkeypatch.setattr(compat, "pytest_version", parse_version("9.1.0"))
    request = mock.Mock()

    compat.inject_fixture(request, "my_fixture", "my_value")

    _, kwargs = request._fixturemanager._register_fixture.call_args
    assert kwargs["name"] == "my_fixture"
    assert kwargs["node"] is request.node
    assert "nodeid" not in kwargs
    assert kwargs["func"]() == "my_value"


def test_inject_fixture_uses_nodeid_before_pytest_9_1(monkeypatch):
    """inject_fixture keeps passing ``nodeid=`` on pytest < 9.1."""
    monkeypatch.setattr(compat, "pytest_version", parse_version("9.0.0"))
    request = mock.Mock()
    request.node.nodeid = "test_foo.py::test_bar"

    compat.inject_fixture(request, "my_fixture", "my_value")

    _, kwargs = request._fixturemanager._register_fixture.call_args
    assert kwargs["name"] == "my_fixture"
    assert kwargs["nodeid"] == "test_foo.py::test_bar"
    assert "node" not in kwargs
    assert kwargs["func"]() == "my_value"
