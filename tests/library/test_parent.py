"""Test givens declared in the parent conftest and plugin files.

Check the parent givens are collected and overridden in the local conftest.
"""
import textwrap

from pytest_bdd.utils import collect_dumped_objects


def test_parent(testdir):
    """Test parent given is collected.

    Both fixtures come from the parent conftest.
    """
    testdir.makefile(
        ".feature",
        parent=textwrap.dedent(
            """\
            Feature: Parent
                Scenario: Parenting is easy
                    Given I have a parent fixture
                    And I have an overridable fixture
            """
        ),
    )

    testdir.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given


        @given("I have a parent fixture", target_fixture="parent")
        def _():
            return "parent"


        @given("I have an overridable fixture", target_fixture="overridable")
        def _():
            return "parent"

        """
        )
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import scenario

        @scenario("parent.feature", "Parenting is easy")
        def test_parent(request):
            assert request.getfixturevalue("parent") == "parent"
            assert request.getfixturevalue("overridable") == "parent"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_global_when_step(testdir):
    """Test when step defined in the parent conftest."""

    testdir.makefile(
        ".feature",
        global_when=textwrap.dedent(
            """\
            Feature: Global when
                Scenario: Global when step defined in parent conftest
                    When I use a when step from the parent conftest
            """
        ),
    )

    testdir.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import when
        from pytest_bdd.utils import dump_obj

        @when("I use a when step from the parent conftest")
        def _():
            dump_obj("global when step")
        """
        )
    )

    testdir.mkpydir("subdir").join("test_global_when.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import scenarios

            scenarios("../global_when.feature")
            """
        )
    )

    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    [collected_object] = collect_dumped_objects(result)
    assert collected_object == "global when step"


def test_child(testdir):
    """Test the child conftest overriding the fixture."""
    testdir.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given


        @given("I have a parent fixture", target_fixture="parent")
        def _():
            return "parent"


        @given("I have an overridable fixture", target_fixture="overridable")
        def main_conftest():
            return "parent"

        """
        )
    )

    subdir = testdir.mkpydir("subdir")

    subdir.join("conftest.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import given

            @given("I have an overridable fixture", target_fixture="overridable")
            def subdir_conftest():
                return "child"

            """
        )
    )

    subdir.join("child.feature").write(
        textwrap.dedent(
            """\
            Feature: Child
                Scenario: Happy childhood
                    Given I have a parent fixture
                    And I have an overridable fixture
            """
        ),
    )

    subdir.join("test_library.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import scenario


            @scenario("child.feature", "Happy childhood")
            def test_override(request):
                assert request.getfixturevalue("parent") == "parent"
                assert request.getfixturevalue("overridable") == "child"

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


        @given("I have a parent fixture", target_fixture="parent")
        def _():
            return "parent"


        @given("I have an overridable fixture", target_fixture="overridable")
        def _():
            return "parent"

        """
        )
    )

    subdir = testdir.mkpydir("subdir")

    subdir.join("local.feature").write(
        textwrap.dedent(
            """\
            Feature: Local
                Scenario: Local override
                    Given I have a parent fixture
                    And I have an overridable fixture
            """
        ),
    )

    subdir.join("test_library.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import given, scenario


            @given("I have an overridable fixture", target_fixture="overridable")
            def _():
                return "local"


            @given("I have a parent fixture", target_fixture="parent")
            def _():
                return "local"


            @scenario("local.feature", "Local override")
            def test_local(request):
                assert request.getfixturevalue("parent") == "local"
                assert request.getfixturevalue("overridable") == "local"
        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_specific_step_overrides_parent_step(testdir):
    testdir.makefile(
        ".feature",
        specific=textwrap.dedent(
            """\
            Feature: Specificity of steps
                Scenario: Overlapping steps 1
                    When I have a specific thing
                    Then the value should be specific test_a

                Scenario: Overlapping steps 2
                    When I have a generic thing
                    Then the value should be generic
            """
        ),
    )

    testdir.makeconftest(
        textwrap.dedent(
            """\
            from pytest_bdd import parsers, when, then
            import pytest


            @pytest.fixture
            def value():
                return []


            @when(parsers.parse("I have a {thing} thing"))
            def in_conftest(thing, value):
                value.append(thing)


            @then(parsers.parse("The value should be {thing}"))
            def check(thing, value):
                assert value == [thing]
        """
        )
    )

    testdir.makepyfile(
        test_a=textwrap.dedent(
            """\
            from pytest_bdd import scenarios, when, parsers


            scenarios("specific.feature")


            @when(parsers.parse("I have a specific thing"))
            def in_test_a(value):
                value.append("specific test_a")

            """
        )
    )

    # Adding a file that will be collected after test_a and that defines the same step name,
    # but it should not be taken into account.
    testdir.makepyfile(
        test_b=textwrap.dedent(
            """\
            from pytest_bdd import when, parsers

            @when(parsers.parse("I have a {thing} thing"))
            def in_test_b(value, thing):
                value.append(thing + " test_b")

            """
        )
    )

    # Adding a file in a subdir that will be collected after test_a and that defines the same step name,
    # but it should not be taken into account.
    # We place it in a subdir so that we are sure that it's collected after test_a, otherwise it may just depend
    # on the filesystem default ordering.
    testdir.mkpydir("zzsubdir").join("test_unrelated.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import when, parsers

            @when(parsers.parse("I have a {thing} thing"))
            def in_zzsubdir_testunrelated(value, thing):
                value.append(thing + " zzsubdir/test_unrelated")

            """
        )
    )
    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=2)
