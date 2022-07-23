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


def test_uses_correct_step_in_the_hierarchy(testdir):
    """
    Test regression found in issue #524, where we couldn't find the correct step implemntation in the
    hierarchy of files/folder as expected.
    This test uses many files and folders that act as decoy, while the real step implementation is defined
    in the last file (test_b/test_b.py).
    """
    testdir.makefile(
        ".feature",
        specific=textwrap.dedent(
            """\
            Feature: Specificity of steps
                Scenario: Overlapping steps
                    Given I have a specific thing
                    Then pass
            """
        ),
    )

    testdir.makeconftest(
        textwrap.dedent(
            """\
            from pytest_bdd import parsers, given, then
            from pytest_bdd.utils import dump_obj
            import pytest

            @given(parsers.parse("I have a {thing} thing"))
            def root_conftest(thing):
                dump_obj(thing + " root_conftest")

            @then("pass")
            def _():
                pass
        """
        )
    )

    # Adding deceiving @when steps around the real test, so that we can check if the right one is used
    # the right one is the one in test_b/test_b.py
    # We purposefully use test_a and test_c as decoys (while test_b/test_b is "good one"), so that we can test that
    # we pick the right one.
    testdir.makepyfile(
        test_a="""\
        from pytest_bdd import given, parsers
        from pytest_bdd.utils import dump_obj

        @given(parsers.re("(?P<thing>.*)"))
        def in_root_test_a_catch_all(thing):
            dump_obj(thing + " (catchall) test_a")

        @given(parsers.parse("I have a specific thing"))
        def in_root_test_a_specific(thing):
            dump_obj(thing + " (specific) test_a")

        @given(parsers.parse("I have a {thing} thing"))
        def in_root_test_a(thing):
            dump_obj(thing + " root_test_a")
        """
    )
    testdir.makepyfile(
        test_c="""\
        from pytest_bdd import given, parsers
        from pytest_bdd.utils import dump_obj

        @given(parsers.re("(?P<thing>.*)"))
        def in_root_test_c_catch_all(thing):
            dump_obj(thing + " (catchall) test_c")

        @given(parsers.parse("I have a specific thing"))
        def in_root_test_c_specific(thing):
            dump_obj(thing + " (specific) test_c")

        @given(parsers.parse("I have a {thing} thing"))
        def in_root_test_c(thing):
            dump_obj(thing + " root_test_b")
        """
    )

    test_b_folder = testdir.mkpydir("test_b")

    # More decoys: test_b/test_a.py and test_b/test_c.py
    test_b_folder.join("test_a.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import given, parsers
            from pytest_bdd.utils import dump_obj

            @given(parsers.re("(?P<thing>.*)"))
            def in_root_test_b_test_a_catch_all(thing):
                dump_obj(thing + " (catchall) test_b_test_a")

            @given(parsers.parse("I have a specific thing"))
            def in_test_b_test_a_specific(thing):
                dump_obj(thing + " (specific) test_b_test_a")

            @given(parsers.parse("I have a {thing} thing"))
            def in_test_b_test_a(thing):
                dump_obj(thing + " test_b_test_a")

            """
        )
    )
    test_b_folder.join("test_c.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import given, parsers
            from pytest_bdd.utils import dump_obj

            @given(parsers.re("(?P<thing>.*)"))
            def in_root_test_b_test_c_catch_all(thing):
                dump_obj(thing + " (catchall) test_b_test_c")

            @given(parsers.parse("I have a specific thing"))
            def in_test_b_test_c_specific(thing):
                dump_obj(thing + " (specific) test_a_test_c")

            @given(parsers.parse("I have a {thing} thing"))
            def in_test_b_test_c(thing):
                dump_obj(thing + " test_c_test_a")

            """
        )
    )

    # Finally, the file with the actual step definition that should be used
    test_b_folder.join("test_b.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import scenarios, given, parsers
            from pytest_bdd.utils import dump_obj


            scenarios("../specific.feature")


            # Important here to have the parse argument different from the others,
            # otherwise test would succeed even if the wrong step was used.
            @given(parsers.parse("I have a {t} thing"))
            def in_test_b_test_b(t):
                dump_obj(f"{t} test_b_test_b")

            """
        )
    )

    result = testdir.runpytest("-s")
    result.assert_outcomes(passed=1)

    [thing] = collect_dumped_objects(result)
    assert thing == "specific test_b_test_b"
