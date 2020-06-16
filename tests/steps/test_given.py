"""Given tests."""
import pytest
import textwrap

from pytest_bdd import given, then, scenario
from pytest_bdd.steps import StepError


def test_root_alias(testdir):
    testdir.makefile(
        ".feature",
        given=textwrap.dedent(
            """\
            Feature: Given
                Scenario: Test reusing root fixture
                    Given I have an alias to the root fixture
                    Then root should be "root"
            """
        ),
    )
    testdir.makeconftest(
        textwrap.dedent(
            """\
        from pytest_bdd import given

        @given("I have a root fixture")
        def root():
            return "root"
        """
        )
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, then, scenario

        @scenario("given.feature", "Test reusing root fixture")
        def test_given():
            pass


        given("I have an alias to the root fixture", fixture="root")


        @then('root should be "root"')
        def root_is_root(root):
            assert root == "root"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_given_with_fixture(testdir):
    testdir.makefile(
        ".feature",
        given=textwrap.dedent(
            """\
            Feature: Given
                Scenario: Test reusing local fixture
                    Given I have alias for foo
                    Then foo should be "foo"
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, then, scenario

        @scenario("given.feature", "Test reusing local fixture")
        def test_given():
            pass


        @given("I have foo")
        def foo():
            return "foo"


        given("I have alias for foo", fixture="foo")


        @then('foo should be "foo"')
        def foo_is_foo(foo):
            assert foo == "foo"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_session_given(testdir):
    testdir.makefile(
        ".feature",
        given=textwrap.dedent(
            """\
            Feature: Given
                Scenario: Test session given
                    Given I have session foo
                    Then session foo should be "session foo"
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, then, scenario

        @scenario("given.feature", "Test session given")
        def test_given():
            pass


        @given("I have session foo", scope="session")
        def session_foo():
            return "session foo"


        @then('session foo should be "session foo"')
        def session_foo_is_foo(session_foo):
            assert session_foo == "session foo"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_given_injection(testdir):
    testdir.makefile(
        ".feature",
        given=textwrap.dedent(
            """\
            Feature: Given
                Scenario: Test given fixture injection
                    Given I have injecting given
                    Then foo should be "injected foo"
            """
        ),
    )
    testdir.makepyfile(
        textwrap.dedent(
            """\
        import pytest
        from pytest_bdd import given, then, scenario

        @scenario("given.feature", "Test given fixture injection")
        def test_given():
            pass

        @given("I have injecting given", target_fixture="foo")
        def injecting_given():
            return "injected foo"


        @then('foo should be "injected foo"')
        def foo_is_injected_foo(foo):
            assert foo == "injected foo"

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_decorate_with_fixture(testdir):
    """Test given can't be used as decorator when the fixture is specified."""
    testdir.makepyfile(
        textwrap.dedent(
            """\
        from pytest_bdd import given

        @given("Foo", fixture="foo")
        def bla():
            pass

        """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(error=1)
    result.stdout.fnmatch_lines("*StepError: Cannot be used as a decorator when the fixture is specified*")
