import textwrap


def test_hooks(testdir):
    testdir.makeconftest("")

    subdir = testdir.mkpydir("subdir")
    subdir.join("conftest.py").write(textwrap.dedent(r"""
        def pytest_pyfunc_call(pyfuncitem):
            print('\npytest_pyfunc_call hook')

        def pytest_generate_tests(metafunc):
            print('\npytest_generate_tests hook')
    """))

    subdir.join("test_foo.py").write(textwrap.dedent(r"""
        from pytest_bdd import scenario

        @scenario('foo.feature', 'Some scenario')
        def test_foo():
            pass
    """))

    subdir.join("foo.feature").write(textwrap.dedent(r"""
        Feature: The feature
        Scenario: Some scenario
    """))

    result = testdir.runpytest("-s")

    assert result.stdout.lines.count('pytest_pyfunc_call hook') == 1
    assert result.stdout.lines.count('pytest_generate_tests hook') == 1
