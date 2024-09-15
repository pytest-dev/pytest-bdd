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
        )
    ],
)
def test_multiline(pytester, feature_text, expected_text):
    pytester.makefile(".feature", multiline=feature_text)

    pytester.makepyfile(
        textwrap.dedent(
            """\
            from pytest_bdd import parsers, given, then, scenario

            expected_text = '''{expected_text}'''


            @scenario("multiline.feature", "Multiline step using sub indentation")
            def test_multiline(request):
                assert request.getfixturevalue("text") == expected_text


            @given(parsers.parse("I have a step with:\\n{{text}}"), target_fixture="text")
            def _(text):
                return text


            @then("the text should be parsed with correct indentation")
            def _(text):
                assert text == expected_text

            """.format(
                expected_text=expected_text.encode("unicode_escape").decode("utf-8"),
            )
        )
    )
    result = pytester.runpytest()
    result.assert_outcomes(passed=1)
