"""Main command."""

from __future__ import annotations

import os
import sys
import textwrap

from pytest_bdd.scripts import main

PATH = os.path.dirname(__file__)


def test_main(monkeypatch, capsys):
    """Test if main command shows help when called without the subcommand."""
    monkeypatch.setattr(sys, "argv", ["pytest-bdd"])
    monkeypatch.setattr(sys, "exit", lambda x: x)
    main()
    out, err = capsys.readouterr()
    assert "usage: pytest-bdd [-h]" in err
    assert "pytest-bdd: error:" in err


def test_step_definitions_found_using_main(pytester):
    """Issue 173: Ensure step definitions are found when using pytest.main."""
    pytester.makefile(
        ".feature",
        outline=textwrap.dedent(
            """\
            Feature: Outlined Scenarios

                Scenario Outline: Outlined given, when, then
                    Given there are <start> cucumbers
                    When I eat <eat> cucumbers
                    Then I should have <left> cucumbers

                    Examples:
                        | start | eat | left |
                        |  12   |  5  |  7   |
            """
        ),
    )

    pytester.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import given, when, then, parsers, scenarios

            scenarios(".")

            @given(parsers.parse("there are {start:d} cucumbers"), target_fixture="cucumbers")
            def _(start):
                assert isinstance(start, int)
                return {"start": start}


            @when(parsers.parse("I eat {eat:g} cucumbers"))
            def _(cucumbers, eat):
                assert isinstance(eat, float)
                cucumbers["eat"] = eat


            @then(parsers.parse("I should have {left} cucumbers"))
            def _(cucumbers, left):
                assert isinstance(left, str)
                assert cucumbers["start"] - cucumbers["eat"] == int(left)
            """
        )
    )

    pytester.makepyfile(
        main=textwrap.dedent(
            """\
            import pytest
            import os

            # Programmatically run pytest
            if __name__ == "__main__":
                pytest.main([os.path.abspath("test_step_definitions_found_using_main.py")])
            """
        )
    )

    result = pytester.runpython(pytester.path / "main.py")
    result.assert_outcomes(passed=1, failed=0)
