"""Test code generation command."""

from __future__ import annotations

import os
import sys
import textwrap

from pytest_bdd.scripts import main

PATH = os.path.dirname(__file__)


def test_migrate(monkeypatch, capsys, pytester):
    """Test if the code is migrated by a given file mask."""
    tests = pytester.mkpydir("tests")

    tests.joinpath("test_foo.py").write_text(
        textwrap.dedent(
            '''
        """Foo bar tests."""
        from pytest_bdd import scenario

        test_foo = scenario('foo_bar.feature', 'Foo bar')
    '''
        )
    )

    monkeypatch.setattr(sys, "argv", ["", "migrate", str(tests)])
    main()
    out, err = capsys.readouterr()
    out = "\n".join(sorted(out.splitlines()))
    expected = textwrap.dedent(
        """
    migrated: {0}/test_foo.py
    skipped: {0}/__init__.py""".format(str(tests))[1:]
    )
    assert out == expected
    assert tests.joinpath("test_foo.py").read_text() == textwrap.dedent(
        '''
    """Foo bar tests."""
    from pytest_bdd import scenario

    @scenario('foo_bar.feature', 'Foo bar')
    def test_foo():
        pass
    '''
    )
