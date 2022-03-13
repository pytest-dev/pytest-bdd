from __future__ import annotations

import os.path
import pkgutil
import textwrap
from collections import OrderedDict
from typing import TYPE_CHECKING

import lark
from lark import Lark, Token, Tree, v_args
from lark.indenter import Indenter

from pytest_bdd import types as pytest_bdd_types
from pytest_bdd.parser import Background, Examples, Feature, Scenario, ScenarioTemplate, Step, split_line

if TYPE_CHECKING:
    from typing import Sequence, TypeAlias

# TODOs:
#  - line numbers don't seem to work correctly.

TableType: TypeAlias = list[tuple[str, ...]]


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


def extract_text_from_step_docstring(docstring):
    content = docstring[4:-3]
    dedented = textwrap.dedent(content)
    assert dedented[-1] == "\n"
    dedented_without_newline = dedented[:-1]
    return dedented_without_newline


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
            raise ValueError("Invalid indentation")  # TODO: Raise a better custom error
        elif indentation_diff > 0:
            # If the difference is positive, it means that the content has more indentation,
            # so we should add the difference back to it.
            content = "\n".join(" " * indentation_diff + line for line in dedented.split("\n"))
        else:
            # Otherwise, there is no difference; nothing to do.
            content = dedented

        # Remove the marker we added initially.
        suffix = f"\n{EOF_MARKER}"
        assert content.endswith(suffix)
        content = content[: -len(suffix)]

        return content

    @v_args(inline=True)
    def step_arg(self, docstring: str | None, step_datatable) -> tuple[str, str]:
        return docstring, step_datatable

    def givens(self, steps: list[Tree]) -> tuple[str, list[Tree]]:
        return pytest_bdd_types.GIVEN, steps

    def whens(self, steps: list[Tree]) -> tuple[str, list[Tree]]:
        return pytest_bdd_types.WHEN, steps

    def thens(self, steps: list[Tree]) -> tuple[str, list[Tree]]:
        return pytest_bdd_types.THEN, steps

    @v_args(inline=True)
    def step(
        self, type: Token, name: Token, docstring: Token | None = None, datatable: TableType | None = None
    ) -> tuple[Token, str, str, TableType]:
        return type, name, docstring, datatable

    def steps(self, step_groups: list[tuple[str, tuple[Token, str, str, TableType]]]) -> list[Step]:
        steps = [
            Step(
                name=str(value_token),
                type=bdd_type,
                line_number=type_token.line,
                indent=type_token.column,
                keyword=str(type_token.strip()),
                docstring=docstring,
                datatable=datatable,
            )
            for bdd_type, step_group in step_groups
            for type_token, value_token, docstring, datatable in step_group
        ]
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
        # TODO: Validate lengths
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

    # def EXAMPLE_STRING(self, value):
    #     return value

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


def parse(content: str) -> Feature:
    if content[-1] != "\n":
        # Fix for the Indenter not working well when thers is no \n at the end of file
        # See https://github.com/lark-parser/lark/issues/321
        content += "\n"
    tree = parser.parse(content)
    print(tree.pretty())  # TODO: Remove before merge
    gherkin = TreeToGherkin().transform(tree)
    return gherkin


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

    feature = parse(content)
    feature.filename = abs_filename
    feature.rel_filename = rel_filename

    feature.validate()

    return feature
