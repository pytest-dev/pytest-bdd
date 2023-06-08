import textwrap


def test_hooks(testdir):
    subdir = testdir.mkpydir("subdir")
    subdir.join("conftest.py").write(
        textwrap.dedent(
            # language=python
            r"""
            def pytest_pyfunc_call(pyfuncitem):
                print('\npytest_pyfunc_call hook')

            def pytest_generate_tests(metafunc):
                print('\npytest_generate_tests hook')
            """
        )
    )

    subdir.join("foo.feature").write(
        textwrap.dedent(
            # language=gherkin
            r"""
            Feature: The feature
                Scenario: Some scenario
            """
        )
    )

    result = testdir.runpytest("-s")

    assert result.stdout.lines.count("pytest_pyfunc_call hook") == 1
    assert result.stdout.lines.count("pytest_generate_tests hook") == 1


def test_item_collection_does_not_break_on_non_function_items(testdir):
    """Regression test for https://github.com/pytest-dev/pytest-bdd/issues/317"""
    testdir.makeconftest(
        # language=python
        """\
        import pytest

        @pytest.hookimpl(tryfirst=True)
        def pytest_collection_modifyitems(session, config, items):
            try:
                item_creator = CustomItem.from_parent  # Only available in pytest >= 5.4.0
            except AttributeError:
                item_creator = CustomItem

            items[:] = [item_creator(name=item.name, parent=item.parent) for item in items]

        class CustomItem(pytest.Item):
            def runtest(self):
                assert True
        """
    )

    testdir.makepyfile(
        # language=python
        """\
        def test_convert_me_to_custom_item_and_assert_true():
            assert False
        """
    )

    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
