# coding: utf-8
"""Tests for testing cases when we have unicode in feature file."""

import sys
import pytest
import functools
import textwrap
from pytest_bdd import given, parsers, scenario, then

scenario = functools.partial(scenario, "unicode.feature")


def test_steps_in_feature_file_have_unicode(testdir):
    testdir.makefile(
        ".feature",
        unicode=textwrap.dedent(
            u"""\
            Feature: Юнікодні символи

                Scenario: Кроки в .feature файлі містять юнікод
                    Given у мене є рядок який містить 'якийсь контент'
                    Then I should see that the string equals to content 'якийсь контент'

                Scenario: Given names have unicode types
                    Given I have an alias with a unicode type for foo
                    Then foo should be "foo"
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            u"""\
        import sys
        import pytest
        from pytest_bdd import parsers, given, then, scenario

        @scenario("unicode.feature", "Кроки в .feature файлі містять юнікод")
        def test_unicode():
            pass

        @pytest.fixture
        def string():
            \"\"\"String fixture.\"\"\"
            return {"content": ""}


        @given(parsers.parse(u"у мене є рядок який містить '{content}'"))
        def there_is_a_string_with_content(content, string):
            \"\"\"Create string with unicode content.\"\"\"
            string["content"] = content


        given(u"I have an alias with a unicode type for foo", fixture="foo")


        @then(parsers.parse("I should see that the string equals to content '{content}'"))
        def assert_that_the_string_equals_to_content(content, string):
            \"\"\"Assert that the string equals to content.\"\"\"
            assert string["content"] == content
            if sys.version_info < (3, 0):
                assert isinstance(content, unicode)
        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 0


def test_steps_in_py_file_have_unicode(testdir):
    testdir.makefile(
        ".feature",
        unicode=textwrap.dedent(
            u"""\
            Feature: Юнікодні символи

                Scenario: Steps in .py file have unicode
                        Given there is an other string with content 'якийсь контент'
                        Then I should see that the other string equals to content 'якийсь контент'
            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            u"""\
        import pytest
        from pytest_bdd import given, then, scenario

        @scenario("unicode.feature", "Steps in .py file have unicode")
        def test_unicode():
            pass

        @pytest.fixture
        def string():
            \"\"\"String fixture.\"\"\"
            return {"content": ""}


        @given("there is an other string with content 'якийсь контент'")
        def there_is_an_other_string_with_content(string):
            \"\"\"Create other string with unicode content.\"\"\"
            string["content"] = u"с каким-то контентом"

        @then("I should see that the other string equals to content 'якийсь контент'")
        def assert_that_the_other_string_equals_to_content(string):
            \"\"\"Assert that the other string equals to content.\"\"\"
            assert string["content"] == u"с каким-то контентом"

        """
        )
    )
    result = testdir.runpytest()
    assert result.ret == 0
