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
            "   Some\n\n Extra\nLines",
        ),
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

            '''
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
                pass


            @given(parsers.parse("I have a step with:"), target_fixture="text")
            def i_have_text(step):
                return step.doc_string.content


            @then("the text should be parsed with correct indentation")
            def text_should_be_correct(text):
                assert text == expected_text

            """.format(
                expected_text=expected_text.encode("unicode_escape").decode("utf-8"),
            )
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)
