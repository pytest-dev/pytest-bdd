import textwrap


def test_arg_fixture_mix(testdir):

    subdir = testdir.mkpydir("arg_fixture_mix")
    subdir.join("test_a.py").write(
        textwrap.dedent(
            """\
        import re
        import pytest
        from pytest_bdd import scenario, given, then, parsers


        @pytest.fixture
        def foo():
            return "fine"

        @scenario(
            'arg_and_fixture_mix.feature',
            'Use the step argument with the same name as fixture of another test',
        )
        def test_args():
            pass

        @given(parsers.parse('foo is "{foo}"'))
        def foo1(foo):
            pass


        @then(parsers.parse('foo should be "{foo_value}"'))
        def foo_should_be(foo, foo_value):
            assert foo == foo_value

        @scenario(
            'arg_and_fixture_mix.feature',
            'Everything is fine',
        )
        def test_bar():
            pass

        @given('it is all fine')
        def fine():
            return "fine"


        @then('foo should be fine')
        def foo_should_be_fine(foo):
            assert foo == "fine"
    """
        )
    )

    subdir.join("test_b.py").write(
        textwrap.dedent(
            """\
        import re
        import pytest
        from pytest_bdd import scenario, given, then

        @scenario(
            'arg_and_fixture_mix.feature',
            'Everything is fine',
        )
        def test_args():
            pass

        @pytest.fixture
        def foo():
            return "fine"


        @given('it is all fine')
        def fine():
            return "fine"


        @then('foo should be fine')
        def foo_should_be(foo):
            assert foo == "fine"


        def test_bar(foo):
            assert foo == 'fine'
    """
        )
    )

    subdir.join("arg_and_fixture_mix.feature").write(
        """
        Feature: Arg and fixture mix
            Scenario: Use the step argument with the same name as fixture of another test
            Given foo is "Hello"
            Then foo should be "Hello"


            Scenario: Everything is fine
                Given it is all fine
                Then foo should be fine
    """
    )

    result = testdir.runpytest("-k arg_fixture_mix")
    result.assert_outcomes(passed=4)
