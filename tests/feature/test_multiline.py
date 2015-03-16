"""Multiline steps tests."""
import textwrap

import pytest

from pytest_bdd import (
    exceptions,
    given,
    parsers,
    scenario,
    then,
)


@pytest.mark.parametrize(["feature_text", "expected_text"], [
    (
        textwrap.dedent("""
        Scenario: Multiline step using sub indentation
            Given I have a step with:
                Some

                Extra
                Lines
            Then the text should be parsed with correct indentation
        """),
        textwrap.dedent("""
        Some

        Extra
        Lines
        """)[1: -1]
    ),
    (
        textwrap.dedent("""
        Scenario: Multiline step using sub indentation
            Given I have a step with:
                Some

              Extra
             Lines

            Then the text should be parsed with correct indentation
        """),
        textwrap.dedent("""
           Some

         Extra
        Lines
        """)[1:-1]
    ),
    (
        textwrap.dedent("""
        Feature:
        Scenario: Multiline step using sub indentation
            Given I have a step with:
                Some
                Extra
                Lines

        """),
        textwrap.dedent("""
        Some
        Extra
        Lines
        """)[1:-1]
    ),
])
def test_multiline(request, tmpdir, feature_text, expected_text):
    file_name = tmpdir.join('test.feature')
    with file_name.open('w') as fd:
        fd.write(feature_text)

    @scenario(file_name.strpath, 'Multiline step using sub indentation')
    def test_multiline(request):
        assert request.getfuncargvalue('i_have_text') == expected_text
    test_multiline(request)


@given(parsers.parse('I have a step with:\n{text}'))
def i_have_text(text):
    return text


@then('the text should be parsed with correct indentation')
def text_should_be_correct(i_have_text, text, expected_text):
    assert i_have_text == text == expected_text


def test_multiline_wrong_indent(request):
    """Multiline step using sub indentation wrong indent."""
    @scenario(
        'multiline.feature',
        'Multiline step using sub indentation wrong indent',
    )
    def test_multiline():
        pass
    with pytest.raises(exceptions.StepDefinitionNotFoundError):
        test_multiline(request)
