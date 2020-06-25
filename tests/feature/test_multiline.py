"""Multiline steps tests."""
import textwrap

import pytest


@pytest.mark.parametrize(
    ["feature_text", "expected_text"],
    [
        (
            textwrap.dedent(
                '''\
            Feature: Multiline
                Scenario: Multiline step using sub indentation
                    Given I have a step with:
                        """
                        Some

                        Extra
                        Lines
                        """
                    Then the text should be parsed with correct indentation
            '''
            ),
            "Some\n\nExtra\nLines",
        ),
        (
            textwrap.dedent(
                """\
            Feature: Multiline
                Scenario: Multiline step using sub indentation
                    Given I have a step with:
                        Some

                        Extra
                        Lines
                    Then the text should be parsed with correct indentation
            """
            ),
            "Some\n\nExtra\nLines",
        ),
        (
            textwrap.dedent(
                """\
            Feature: Multiline
                Scenario: Multiline step using sub indentation
                    Given I have a step with:
                        Some

                      Extra
                     Lines

                    Then the text should be parsed with correct indentation
            """
            ),
            "   Some\n\n Extra\nLines",
        ),
        (
            textwrap.dedent(
                """\
            Feature: Multiline
                Scenario: Multiline step using sub indentation
                    Given I have a step with:
                        Some
                        Extra
                        Lines

            """
            ),
            "Some\nExtra\nLines",
        ),
    ],
)
def test_multiline(testdir, feature_text, expected_text):
    testdir.makefile(".feature", multiline=feature_text)

    testdir.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import parsers, given, then, scenario

            expected_text = '''{expected_text}'''


            @scenario("multiline.feature", "Multiline step using sub indentation")
            def test_multiline(request):
                assert request.getfixturevalue("text") == expected_text


            @given(parsers.parse("I have a step with:\\n{{text}}"), target_fixture="i_have_text")
            def i_have_text(text):
                return text


            @then("the text should be parsed with correct indentation")
            def text_should_be_correct(i_have_text, text):
                assert i_have_text == text == expected_text

            """.format(
                expected_text=expected_text.encode("unicode_escape").decode("utf-8"),
            )
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


def test_multiline_wrong_indent(testdir):
    """Multiline step using sub indentation wrong indent."""

    testdir.makefile(
        ".feature",
        multiline=textwrap.dedent(
            """\

            Feature: Multiline
                Scenario: Multiline step using sub indentation wrong indent
                    Given I have a step with:
                        Some

                    Extra
                    Lines
                    Then the text should be parsed with correct indentation

            """
        ),
    )

    testdir.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import parsers, given, then, scenario


            @scenario("multiline.feature", "Multiline step using sub indentation wrong indent")
            def test_multiline(request):
                pass


            @given(parsers.parse("I have a step with:\\n{{text}}"))
            def i_have_text(text):
                return text


            @then("the text should be parsed with correct indentation")
            def text_should_be_correct(i_have_text, text):
                assert i_have_text == text == expected_text

            """
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines("*StepDefinitionNotFoundError: Step definition is not found:*")
