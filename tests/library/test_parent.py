"""Test givens declared in the parent conftest and plugin files.

Check the parent givens are collected and overriden in the local conftest.
"""
import textwrap


def test_parent(testdir):
    """Test parent given is collected.

    Both fixtures come from the parent conftest.
    """
    testdir.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given


        @given("I have parent fixture")
        def parent():
            return "parent"


        @given("I have overridable parent fixture")
        def overridable():
            return "parent"

        """
        )
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        def test_parent(parent, overridable):
            assert parent == "parent"
            assert overridable == "parent"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_global_when_step(testdir, request):
    """Test when step defined in the parent conftest."""

    testdir.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import when


        @when("I use a when step from the parent conftest")
        def global_when():
            pass

        """
        )
    )

    subdir = testdir.mkpydir("subdir")

    subdir.join("test_library.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd.steps import get_step_fixture_name, WHEN

            def test_global_when_step(request):
                assert request.getfixturevalue(
                    get_step_fixture_name("I use a when step from the parent conftest",
                    WHEN,
                )
            )
        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_child(testdir):
    """Test the child conftest overriding the fixture."""
    testdir.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given


        @given("I have parent fixture")
        def parent():
            return "parent"


        @given("I have overridable parent fixture")
        def overridable():
            return "parent"

        """
        )
    )

    subdir = testdir.mkpydir("subdir")

    subdir.join("conftest.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import given

            @given("I have overridable parent fixture")
            def overridable():
                return "child"

            """
        )
    )

    subdir.join("test_library.py").write(
        textwrap.dedent(
            """\
            def test_override(parent, overridable):
                assert parent == "parent"
                assert overridable == "child"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_local(testdir):
    """Test locally overridden fixtures."""
    testdir.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given


        @given("I have parent fixture")
        def parent():
            return "parent"


        @given("I have overridable parent fixture")
        def overridable():
            return "parent"

        """
        )
    )

    subdir = testdir.mkpydir("subdir")

    subdir.join("test_library.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import given
            from pytest_bdd.steps import get_step_fixture_name, GIVEN


            @given("I have locally overriden fixture")
            def overridable():
                return "local"


            @given("I have locally overriden parent fixture")
            def parent():
                return "local"


            def test_local(request, parent, overridable):
                assert parent == "local"
                assert overridable == "local"

                fixture = request.getfixturevalue(
                    get_step_fixture_name("I have locally overriden fixture", GIVEN)
                )
                assert fixture(request) == "local"

                fixture = request.getfixturevalue(
                    get_step_fixture_name("I have locally overriden parent fixture", GIVEN)
                )
                assert fixture(request) == "local"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
