"""Main command."""

import os
import sys

from pytest_bdd.scripts import main

PATH = os.path.dirname(__file__)


def test_main(monkeypatch, capsys):
    """Test if main commmand shows help when called without the subcommand."""
    monkeypatch.setattr(sys, "argv", ["pytest-bdd"])
    monkeypatch.setattr(sys, "exit", lambda x: x)
    main()
    out, err = capsys.readouterr()
    assert "usage: pytest-bdd [-h]" in err
    assert "pytest-bdd: error:" in err
