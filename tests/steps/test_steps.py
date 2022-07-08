"""Test when and then steps are callables."""

import textwrap


def test_when_then(testdir):
    """Test when and then steps are callable functions.

    This test checks that when and then are not evaluated
    during fixture collection that might break the scenario.
    """
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, when, then
        from pytest_bdd.steps import get_step_fixture_name, WHEN, THEN

        @when("I do stuff")
        def do_stuff():
            pass


        @then("I check stuff")
        def check_stuff():
            pass


        def test_when_then(request):
            do_stuff_ = request.getfixturevalue(get_step_fixture_name("I do stuff", WHEN))
            assert callable(do_stuff_)

            check_stuff_ = request.getfixturevalue(get_step_fixture_name("I check stuff", THEN))
            assert callable(check_stuff_)

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
