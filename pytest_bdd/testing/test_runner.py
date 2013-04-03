"""Tests for pytest-bdd-splinter subplugin."""


def test_pytest_scenario(testdir):
        testdir.makepyfile("""
            from pytest_bdd import scenario

            @scenario('some feature', 'some_feature.txt')
            def test_scenario():
                pass
        """)
        result = testdir.runpytest("-v")
        result.stdout.fnmatch_lines([
            "*test_browser*PASS*",
        ])
