"""Multiline steps tests."""

from pytest import mark, param


@mark.parametrize(
    "parser,",
    [
        param("Parser", marks=[mark.deprecated, mark.surplus]),
    ],
)
@mark.parametrize(
    ["feature_text", "expected_text"],
    [
        (
            """\
            Feature: Multiline
                Scenario: Multiline step using sub indentation
                    Given I have a step with:
                        Some

                        Extra
                        Lines
                    Then the text should be parsed with correct indentation
            """,
            "Some\n\nExtra\nLines",
        ),
        (
            """\
            Feature: Multiline
                Scenario: Multiline step using sub indentation
                    Given I have a step with:
                        Some

                      Extra
                     Lines
                    Then the text should be parsed with correct indentation
            """,
            "   Some\n\n Extra\nLines",
        ),
        (
            """\
            Feature: Multiline
                Scenario: Multiline step using sub indentation
                    Given I have a step with:
                        Some
                        Extra
                        Lines
            """,
            "Some\nExtra\nLines",
        ),
    ],
)
def test_multiline(testdir, feature_text, expected_text, parser):
    testdir.makefile(".feature", multiline=feature_text)

    testdir.makepyfile(
        """\
        from pytest_bdd import parsers, given, then, scenario
        from pytest_bdd.parser import {parser} as Parser

        expected_text = '''{expected_text}'''


        @scenario("multiline.feature", "Multiline step using sub indentation", parser=Parser())
        def test_multiline(request):
            pass


        @given(parsers.parse("I have a step with:\\n{{text}}"), target_fixture="text")
        def i_have_text(text):
            return text


        @then("the text should be parsed with correct indentation")
        def text_should_be_correct(text):
            assert text == expected_text
        """.format(
            expected_text=expected_text.encode("unicode_escape").decode("utf-8"),
            parser=parser,
        )
    )
    result = testdir.runpytest()
    result.assert_outcomes(passed=1)


@mark.parametrize(
    "parser,",
    [
        param("Parser", marks=[mark.deprecated, mark.surplus]),
    ],
)
def test_multiline_wrong_indent(testdir, parser):
    """Multiline step using sub indentation wrong indent."""

    testdir.makefile(
        ".feature",
        multiline="""\
            Feature: Multiline
                Scenario: Multiline step using sub indentation wrong indent
                    Given I have a step with:
                        Some

                    Extra
                    Lines
                    Then the text should be parsed with correct indentation
            """,
    )

    testdir.makepyfile(
        f"""\
        from pytest_bdd import parsers, given, then, scenario
        from pytest_bdd.parser import {parser} as Parser


        @scenario("multiline.feature", "Multiline step using sub indentation wrong indent", parser=Parser())
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
    result = testdir.runpytest()
    result.assert_outcomes(failed=1)
    result.stdout.fnmatch_lines("*StepDefinitionNotFoundError: Step definition is not found:*")
