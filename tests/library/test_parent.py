"""Test givens declared in the parent conftest and plugin files.

Check the parent givens are collected and overridden in the local conftest.
"""
import textwrap
from textwrap import dedent


def test_parent(testdir, tmp_path):
    """Test parent given is collected.

    Both fixtures come from the parent conftest.
    """
    (tmp_path / "parent.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
            Feature: Parent
                Scenario: Parenting is easy
                    Given I have a parent fixture
                    And I have an overridable fixture
            """
        )
    )

    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given("I have a parent fixture", target_fixture="parent")
        def parent():
            return "parent"

        @given("I have an overridable fixture", target_fixture="overridable")
        def overridable():
            return "parent"
        """
    )

    testdir.makepyfile(
        # language=python
        f"""\
        from pytest_bdd import scenario
        from pathlib import Path

        @scenario(Path(r"{tmp_path}") / "parent.feature", "Parenting is easy")
        def test_parent(request):
            assert request.getfixturevalue("parent") == "parent"
            assert request.getfixturevalue("overridable") == "parent"
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_child(testdir, tmp_path):
    """Test the child conftest overriding the fixture."""
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given("I have a parent fixture", target_fixture="parent")
        def parent():
            return "parent"

        @given("I have an overridable fixture", target_fixture="overridable")
        def overridable():
            return "parent"
        """
    )

    subdir = testdir.mkpydir("subdir")

    subdir.join("conftest.py").write(
        dedent(
            # language=python
            """\
            from pytest_bdd import given

            @given("I have an overridable fixture", target_fixture="overridable")
            def overridable():
                return "child"

            """
        )
    )

    (tmp_path / "child.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
            Feature: Child
                Scenario: Happy childhood
                    Given I have a parent fixture
                    And I have an overridable fixture
            """
        )
    )

    subdir.join("test_library.py").write(
        dedent(
            # language=python
            f"""\
            from pytest_bdd import scenario
            from pathlib import Path

            @scenario(Path(r"{tmp_path}") / "child.feature", "Happy childhood", features_base_dir='subdir')
            def test_override(request):
                assert request.getfixturevalue("parent") == "parent"
                assert request.getfixturevalue("overridable") == "child"
            """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_local(testdir, tmp_path):
    """Test locally overridden fixtures."""
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given("I have a parent fixture", target_fixture="parent")
        def parent():
            return "parent"

        @given("I have an overridable fixture", target_fixture="overridable")
        def overridable():
            return "parent"
        """
    )

    subdir = testdir.mkpydir("subdir")

    (tmp_path / "local.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
            Feature: Local
                Scenario: Local override
                    Given I have a parent fixture
                    And I have an overridable fixture
            """,
        )
    )

    subdir.join("test_library.py").write(
        dedent(
            # language=python
            f"""\
            from pytest_bdd import given, scenario
            from pathlib import Path

            @given("I have an overridable fixture", target_fixture="overridable")
            def overridable():
                return "local"

            @given("I have a parent fixture", target_fixture="parent")
            def parent():
                return "local"

            @scenario(Path(r"{tmp_path}") / "local.feature", "Local override", features_base_dir='subdir')
            def test_local(request):
                assert request.getfixturevalue("parent") == "local"
                assert request.getfixturevalue("overridable") == "local"
            """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_local_multiple_target_fixtures(testdir, tmp_path):
    """Test locally overridden fixtures."""
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given("I have a parent fixtures", target_fixtures=["parent", "overridable"])
        def parent():
            return "parent1", "parent2"
        """
    )

    subdir = testdir.mkpydir("subdir")

    (tmp_path / "local.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
            Feature: Local
                Scenario: Local override
                    Given I have a parent fixture
            """
        )
    )

    subdir.join("test_library.py").write(
        dedent(
            # language=python
            f"""\
            from pytest_bdd import given, scenario
            from pathlib import Path

            @given("I have a parent fixture", target_fixtures=["parent", "overridable"])
            def parent():
                return "local1", "local2"

            @scenario(Path(r"{tmp_path}") / "local.feature", "Local override", features_base_dir='subdir')
            def test_local(request):
                assert request.getfixturevalue("parent") == "local1"
                assert request.getfixturevalue("overridable") == "local2"
            """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_local_both_target_fixture_and_target_fixtures(testdir, tmp_path):
    """Test locally overridden fixtures."""
    testdir.makeconftest(
        # language=python
        """\
        from pytest_bdd import given

        @given("I have a parent fixtures", target_fixture="parent", target_fixtures=["overridable"])
        def parent():
            return "parent1", "parent2"
        """
    )

    subdir = testdir.mkpydir("subdir")

    (tmp_path / "local.feature").write_text(
        textwrap.dedent(
            # language=gherkin
            """\
            Feature: Local
                Scenario: Local override
                    Given I have a parent fixture
            """,
        )
    )

    subdir.join("test_library.py").write(
        dedent(
            # language=python
            f"""\
            from pytest_bdd import given, scenario
            from pathlib import  Path

            @given("I have a parent fixture", target_fixtures=["parent", "overridable"])
            def parent():
                return "local1", "local2"

            @scenario(Path(r"{tmp_path}") / "local.feature", "Local override")
            def test_local(request):
                assert request.getfixturevalue("parent") == "local1"
                assert request.getfixturevalue("overridable") == "local2"
            """
        )
    )
    result = testdir.runpytest_subprocess("-W", "ignore::pytest_bdd.PytestBDDStepDefinitionWarning")
    result.assert_outcomes(passed=1)
