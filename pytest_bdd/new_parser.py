from __future__ import annotations

import os.path
import pkgutil
import textwrap
from collections import OrderedDict
from typing import TYPE_CHECKING

import lark
from lark import Lark, Token, Tree, UnexpectedInput, v_args
from lark.exceptions import VisitError
from lark.indenter import Indenter

from pytest_bdd import types as pytest_bdd_types
from pytest_bdd.parser import (
    Background,
    Examples,
    Feature,
    Scenario,
    ScenarioTemplate,
    Step,
    ValidationError,
    split_line,
)

if TYPE_CHECKING:
    from typing import Callable, Sequence, TypeAlias

    TableType: TypeAlias = list[tuple[str, ...]]

# TODOs:
#  - line numbers don't seem to work correctly.


class TreeIndenter(Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types = []
    CLOSE_PAREN_types = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 8


grammar = pkgutil.get_data("pytest_bdd", "parser_data/gherkin.grammar.lark").decode("utf-8")
parser = Lark(
    grammar,
    start="start",
    parser="lalr",
    postlex=TreeIndenter(),
    maybe_placeholders=True,
    debug=True,
)


class TreeToGherkin(lark.Transformer):
    @v_args(inline=True)
    def string(self, value: Token) -> Token:
        # TODO: Unescape characters?
        return value

    def given(self, _: Token) -> str:
        return pytest_bdd_types.GIVEN

    def when(self, _: Token) -> str:
        return pytest_bdd_types.WHEN

    def then(self, _: Token) -> str:
        return pytest_bdd_types.THEN

    def step_docstring(self, value: list[Token]) -> str:
        # TODO: Unescape escaped characters?
        # TODO: Try to handle also \r\n
        # TODO: Check if tabs and spaces work?

        EOF_MARKER = "PYTEST_BDD_EOF_DOCSTRING_MARKER"
        [text] = value

        if text.find('"""') == -1:
            quotes = "'''"
        elif text.find("'''") == -1:
            quotes = '"""'
        elif text.find('"""') < text.find("'''"):
            quotes = '"""'
        else:
            quotes = "'''"
        before_quotes, _, after_quotes = text.partition(quotes)
        last_new_line = before_quotes.rfind("\n")
        assert last_new_line >= 0
        indents = before_quotes[last_new_line:]
        column = len(indents) - 1  # because the \n is in the string
        pre, raw_content, post = after_quotes[:1], after_quotes[1:-3], after_quotes[-3:]
        assert pre == "\n"
        assert post in {'"""', "'''"}

        # HACK: We append to the content a non-whitespace marker, so that textwrap.dedent will retain the indentation
        #  of the last line. This will allow us to check the indentation of all lines, including the last one.
        #  We will remove the marker before returning the result.
        raw_content += EOF_MARKER

        dedented = textwrap.dedent(raw_content)

        # Determine the indentation of the content with respect to the indentation of the triple quotes.
        indentation_diff = raw_content.find(dedented.split("\n")[0]) - column
        if indentation_diff < 0:
            # If it is negative, it means that the content had some lines that had less indentation
            # than the triple quotes line. This is an error.
            raise GherkinInvalidDocstring(context=text, line=text.line + 1)
        elif indentation_diff > 0:
            # If the difference is positive, it means that the content has more indentation,
            # so we should add the difference back to it.
            content = "\n".join(" " * indentation_diff + line for line in dedented.split("\n"))
        else:
            # Otherwise, there is no difference; nothing to do.
            content = dedented

        # Remove the marker we added initially.
        suffix = f"\n{EOF_MARKER}"
        if not content.endswith(suffix):
            # At this point, this can happen with a docstring like this:
            # """
            #   Invalid quote indent
            #     """
            raise GherkinInvalidDocstring(context=text, line=text.line + 1)
        content = content[: -len(suffix)]

        return content

    @v_args(inline=True)
    def step_arg(self, docstring: str | None, step_datatable) -> tuple[str, str]:
        return docstring, step_datatable

    def givens(self, steps: list[Callable[[str], Step]]) -> list[Step]:
        return [step_maker(pytest_bdd_types.GIVEN) for step_maker in steps]

    def whens(self, steps: list[Callable[[str], Step]]) -> list[Step]:
        return [step_maker(pytest_bdd_types.WHEN) for step_maker in steps]

    def thens(self, steps: list[Callable[[str], Step]]) -> list[Step]:
        return [step_maker(pytest_bdd_types.THEN) for step_maker in steps]

    @v_args(inline=True)
    def step(
        self, type: Token, name: Token, docstring: Token | None = None, datatable: TableType | None = None
    ) -> Callable[[str], Step]:
        def step_maker(bdd_type: str) -> Step:
            return Step(
                name=str(name),
                type=bdd_type,
                line_number=type.line,
                indent=type.column,
                keyword=str(type.strip()),
                docstring=docstring,
                datatable=datatable,
            )

        return step_maker

    def steps(self, step_groups: list[list[Step]]) -> list[Step]:
        steps = [step for step_group in step_groups for step in step_group]
        return steps

    @v_args(inline=True)
    def scenario_line(self, _: Token, value: Token) -> Token:
        return value

    def tag_lines(self, value: list[Tree]) -> set[str]:
        tags = {el for tag_line in value for el in tag_line.children}
        return tags

    @v_args(inline=True)
    def scenario(self, tag_lines: set[str] | None, scenario_line: Token, steps: list[Step] | None):
        # TODO: Try to remove duplicated code with "scenario_outline"
        scenario = ScenarioTemplate(
            name=scenario_line.strip(),
            line_number=scenario_line.line,
            tags=tag_lines or set(),
            feature=None,  # added later
        )
        for step in steps or []:
            scenario.add_step(step)
        return scenario

    @v_args(inline=True)
    def scenario_outline(
        self, tag_lines: set[str] | None, scenario_line: Token, steps: list[Step] | None, examples: Examples | None
    ):
        scenario = ScenarioTemplate(
            name=scenario_line.strip(),
            line_number=scenario_line.line,
            tags=tag_lines or set(),
            feature=None,  # added later
            examples=examples,
        )
        for step in steps or []:
            scenario.add_step(step)
        return scenario

    @v_args(inline=True)
    def background_line(self, line: Token, value: Token) -> tuple[int, Token]:
        return line.line, value

    @v_args(inline=True)
    def background(self, background_line: tuple[int, Token], steps: list[Step] | None):
        b = Background(feature=None, line_number=background_line[0])
        for step in steps:
            b.add_step(step)
        return b

    @v_args(inline=True)
    def tag(self, value):
        assert value[0] == "@"
        return value[1:]

    def description(self, value: list[Token]) -> str:
        return "\n".join(value)

    def table(self, value: Sequence[Sequence[str]]) -> TableType:
        for i, row in enumerate(value[1:]):
            if len(row) != len(value[0]):
                # TODO: Test this, use a custom exception
                raise ValueError(
                    f"Row #{i} has a mismatch number of cells ({len(row)}). Expected {len(value[0])} cells"
                )

        return [tuple(row) for row in value]

    @v_args(inline=True)
    def table_row(self, value: Token) -> list[str]:
        cells = split_line(value)
        return cells

    @v_args(inline=True)
    def examples(self, example_line: Tree, table: TableType) -> Examples:
        examples_token, title = example_line.children
        ex = Examples()

        ex.line_number = examples_token.line
        ex.name = title
        header, rows = table[0], table[1:]
        ex.set_param_names(header)
        for row in rows:
            ex.add_example(row)
        return ex

    @v_args(inline=True)
    def feature(
        self,
        tag_lines: set[str] | None,
        feature_line: Tree,
        description: str | None,
        background: Background | None,
        scenarios: Tree | None,
    ) -> Feature:

        [_, feature_name] = feature_line.children

        feature = Feature(
            scenarios=OrderedDict(),
            filename=None,
            rel_filename=None,
            name=str(feature_name),
            tags=tag_lines or {},
            background=None,
            line_number=feature_name.line,
            description=description or "",
        )
        if scenarios is not None:
            for scenario in scenarios.children:
                scenario.feature = feature
                feature.scenarios[scenario.name] = scenario

        if background is not None:
            background.feature = feature
            feature.background = background

        return feature


class GherkinSyntaxError(Exception):
    label = "Gherkin syntax error"

    def __init__(self, context: str, line: int, column: int | None = None, filename: str | None = None):
        self.context = context
        self.line = line
        self.column = column
        self.filename = filename

    def __str__(self):
        filename = self.filename if self.filename is not None else "<unknown>"
        message = f"{self.label} at line {self.line}"
        if self.column is not None:
            message += f", column {self.column}"
        message += f":\n\n{self.context}\n\nFile: {filename}"
        return message


class GherkinMultipleFeatures(GherkinSyntaxError):
    label = "Multiple features found"


class GherkinMissingFeatureDefinition(GherkinSyntaxError):
    label = "Missing feature definition"


class GherkinMissingFeatureName(GherkinSyntaxError):
    label = "Missing feature name"


class GherkinInvalidDocstring(GherkinSyntaxError):
    label = "Invalid docstring"


class GherkinUnexpectedInput(GherkinSyntaxError):
    label = "Unexpected input"


class GherkinInvalidTable(GherkinSyntaxError):
    label = "Invalid table"


def parse(content: str, filename: str | None = None) -> Feature:
    if content[-1] != "\n":
        # Fix for the Indenter not working well when there is no \n at the end of file
        # See https://github.com/lark-parser/lark/issues/321
        content += "\n"

    try:
        tree = parser.parse(content)
    except UnexpectedInput as u:
        exc_class = u.match_examples(
            parser.parse,
            {
                GherkinMultipleFeatures: [
                    """\
Feature: a
    Scenario: b
Feature: c
    Scenario: d
""",
                    """\
Feature: a
Feature: c
""",
                ],
                GherkinMissingFeatureDefinition: [
                    """\
Scenario: foo
    Given bar
""",
                ],
                GherkinMissingFeatureName: [
                    "Feature:",
                ],
                GherkinInvalidDocstring: [
                    """\
Feature: foo
    Scenario: bar
        Given baz
            '''
            mismatching quotes
            \"\"\"
""",
                    """\
Feature: foo
    Scenario: bar
        Given baz
            '''
            too much trailing indentation
                '''
""",
                    """\
Feature: foo
    Scenario: bar
        Given baz
            '''
            too few trailing indentation
        '''
                    """,
                ],
                GherkinInvalidTable: [
                    """\
Feature: foo
    Scenario Outline: bar
        Examples:
        | no trailing "pipe" in header (it's escaped) \\|
""",
                    """\
Feature: foo
    Scenario Outline: bar
        Examples:
        | foo |
        | no trailing "pipe" in cell(it's escaped) \\|
""",
                    """\
Feature: foo
    Scenario Outline: bar
        Examples:
        | foo |
        | bar |
        | no trailing "pipe" in cell(it's escaped) \\|
""",
                ],
            },
            use_accepts=True,
        )
        if exc_class is None:
            exc_class = GherkinUnexpectedInput
        raise exc_class(context=u.get_context(content), line=u.line, column=u.column, filename=filename) from u

    print(tree.pretty())  # TODO: Remove before merge

    try:
        feature = TreeToGherkin().transform(tree)
    except VisitError as e:
        original_exc = e.orig_exc
        if isinstance(original_exc, GherkinSyntaxError):
            original_exc.filename = filename
            raise original_exc from None
        raise

    feature.validate()

    return feature


def parse_feature(basedir, filename, encoding="utf-8"):
    """Parse the feature file.

    :param str basedir: Feature files base directory.
    :param str filename: Relative path to the feature file.
    :param str encoding: Feature file encoding (utf-8 by default).
    """
    abs_filename = os.path.abspath(os.path.join(basedir, filename))
    rel_filename = os.path.join(os.path.basename(basedir), filename)

    with open(abs_filename, encoding=encoding) as f:
        content = f.read()

    feature = parse(content, abs_filename)
    feature.filename = abs_filename
    feature.rel_filename = rel_filename

    if feature.filename is None:
        raise ValidationError("Missing filename")
    if feature.rel_filename is None:
        raise ValidationError("Missing rel_filename")

    return feature
