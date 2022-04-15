"""Test givens declared in the parent conftest and plugin files.

Check the parent givens are collected and overridden in the local conftest.
"""
import textwrap


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
        def parent():
            return "parent"


        @given("I have an overridable fixture", target_fixture="overridable")
        def overridable():
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


def test_child(testdir):
    """Test the child conftest overriding the fixture."""
    testdir.makeconftest(
        textwrap.dedent(
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
    )

    subdir = testdir.mkpydir("subdir")

    subdir.join("conftest.py").write(
        textwrap.dedent(
            """\
            from pytest_bdd import given

            @given("I have an overridable fixture", target_fixture="overridable")
            def overridable():
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
        def parent():
            return "parent"


        @given("I have an overridable fixture", target_fixture="overridable")
        def overridable():
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
            def overridable():
                return "local"


            @given("I have a parent fixture", target_fixture="parent")
            def parent():
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


def test_local_multiple_target_fixtures(testdir):
    """Test locally overridden fixtures."""
    testdir.makeconftest(
        textwrap.dedent(
            """\
                from pytest_bdd import given

                @given("I have a parent fixtures", target_fixtures=["parent", "overridable"])
                def parent():
                    return "parent1", "parent2"
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
                """
        ),
    )

    subdir.join("test_library.py").write(
        textwrap.dedent(
            """\
                from pytest_bdd import given, scenario

                @given("I have a parent fixture", target_fixtures=["parent", "overridable"])
                def parent():
                    return "local1", "local2"

                @scenario("local.feature", "Local override")
                def test_local(request):
                    assert request.getfixturevalue("parent") == "local1"
                    assert request.getfixturevalue("overridable") == "local2"
                """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_local_both_target_fixture_and_target_fixtures(testdir):
    """Test locally overridden fixtures."""
    testdir.makeconftest(
        textwrap.dedent(
            """\
                from pytest_bdd import given

                @given("I have a parent fixtures", target_fixture="parent", target_fixtures=["overridable"])
                def parent():
                    return "parent1", "parent2"
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
                """
        ),
    )

    subdir.join("test_library.py").write(
        textwrap.dedent(
            """\
                from pytest_bdd import given, scenario

                @given("I have a parent fixture", target_fixtures=["parent", "overridable"])
                def parent():
                    return "local1", "local2"

                @scenario("local.feature", "Local override")
                def test_local(request):
                    assert request.getfixturevalue("parent") == "local1"
                    assert request.getfixturevalue("overridable") == "local2"
            """
        )
    )
    result = testdir.runpytest_subprocess("-W", "ignore::pytest_bdd.PytestBDDStepDefinitionWarning")
    result.assert_outcomes(passed=1)
