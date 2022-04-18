"""Test code generation command."""

import os
import sys
import textwrap
from pathlib import Path

from pytest_bdd.scripts import main

PATH = os.path.dirname(__file__)


def test_migrate(monkeypatch, capsys, testdir):
    """Test if the code is migrated by a given file mask."""
    tests = testdir.mkpydir("tests")

    tests.join("test_foo.py").write(
        textwrap.dedent(
            '''
        """Foo bar tests."""
        from pytest_bdd import scenario

        test_foo = scenario('foo_bar.feature', 'Foo bar')
    '''
        )
    )

    monkeypatch.setattr(sys, "argv", ["", "migrate", tests.strpath])
    main()
    out, err = capsys.readouterr()
    out = "\n".join(sorted(out.splitlines()))
    expected = textwrap.dedent(
        f"""\
            migrated: {Path(tests.strpath)/'test_foo.py'}
            skipped: {Path(tests.strpath)/'__init__.py'}"""
    )
    assert out == expected
    assert tests.join("test_foo.py").read() == textwrap.dedent(
        '''
    """Foo bar tests."""
    from pytest_bdd import scenario

    @scenario('foo_bar.feature', 'Foo bar')
    def test_foo():
        pass
    '''
    )
