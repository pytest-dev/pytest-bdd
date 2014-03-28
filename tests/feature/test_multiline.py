"""Multiline steps tests."""
import re

from pytest_bdd import given, then, scenario


@scenario(
    'multiline.feature',
    'Multiline step using sub indentation',
)
def test_multiline():
    pass


@given(re.compile(r'I have a step with:\n(?P<text>.+)', re.DOTALL))
def i_have_text(text):
    return text


@then('the text should be parsed with correct indentation')
def eat_cucumbers(i_have_text, text):
    assert i_have_text == text == """Some
Extra
Lines"""
