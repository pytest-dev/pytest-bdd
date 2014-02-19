import py


def test_arg_fixture_mix(testdir):

    subdir = testdir.mkpydir("arg_fixture_mix")
    subdir.join("test_a.py").write(py.code.Source("""
        import re
        import pytest
        from pytest_bdd import scenario, given, then


        @pytest.fixture
        def foo():
            return "fine"


        test_args = scenario(
            'arg_and_fixture_mix.feature',
            'Use the step argument with the same name as fixture of another test',
        )


        @given(re.compile(r'foo is "(?P<foo>\w+)"'))
        def foo1(foo):
            pass


        @then(re.compile(r'foo should be "(?P<foo_value>\w+)"'))
        def foo_should_be(foo, foo_value):
            assert foo == foo_value


        test_bar = scenario(
            'arg_and_fixture_mix.feature',
            'Everything is fine',
        )


        @given(re.compile(r'it is all fine'))
        def fine():
            return "fine"


        @then(re.compile(r'foo should be fine'))
        def foo_should_be_fine(foo):
            assert foo == "fine"
    """))

    subdir.join("test_b.py").write(py.code.Source("""
        import re
        import pytest
        from pytest_bdd import scenario, given, then


        test_args = scenario(
            'arg_and_fixture_mix.feature',
            'Everything is fine',
        )


        @pytest.fixture
        def foo():
            return "fine"


        @given(re.compile(r'it is all fine'))
        def fine():
            return "fine"


        @then(re.compile(r'foo should be fine'))
        def foo_should_be(foo):
            assert foo == "fine"


        def test_bar(foo):
            assert foo == 'fine'
    """))

    subdir.join("arg_and_fixture_mix.feature").write("""
        Scenario: Use the step argument with the same name as fixture of another test
        Given foo is "Hello"
        Then foo should be "Hello"


        Scenario: Everything is fine
            Given it is all fine
            Then foo should be fine
    """)

    result = testdir.runpytest("-k arg_fixture_mix")
    assert result.ret == 0
