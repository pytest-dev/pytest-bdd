"""Tests for testing cases when we have unicode in feature file."""


def test_steps_in_feature_file_have_unicode(testdir):
    testdir.makefile(
        ".feature",
        # language=gherkin
        unicode="""\
            Feature: Юнікодні символи

                Scenario: Кроки в .feature файлі містять юнікод
                    Given у мене є рядок який містить 'якийсь контент'
                    Then I should see that the string equals to content 'якийсь контент'
            """,
    )

    testdir.makeconftest(
        # language=python
        """\
        import pytest

        from pytest_bdd import parsers, given, then

        @pytest.fixture
        def string():
            return {"content": ""}

        @given(parsers.parse(u"у мене є рядок який містить '{content}'"))
        def there_is_a_string_with_content(content, string):
            string["content"] = content

        @then(parsers.parse("I should see that the string equals to content '{content}'"))
        def assert_that_the_string_equals_to_content(content, string):
            assert string["content"] == content
        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_steps_in_py_file_have_unicode(testdir):
    testdir.makefile(
        ".feature",
        # language=gherkin
        unicode="""\
            Feature: Юнікодні символи

                Scenario: Steps in .py file have unicode
                        Given there is an other string with content 'якийсь контент'
                        Then I should see that the other string equals to content 'якийсь контент'
            """,
    )

    testdir.makeconftest(
        # language=python
        """\
        import pytest
        from pytest_bdd import given, then

        @pytest.fixture
        def string():
            return {"content": ""}


        @given("there is an other string with content 'якийсь контент'")
        def there_is_an_other_string_with_content(string):
            string["content"] = u"с каким-то контентом"

        @then("I should see that the other string equals to content 'якийсь контент'")
        def assert_that_the_other_string_equals_to_content(string):
            assert string["content"] == u"с каким-то контентом"

        """
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
