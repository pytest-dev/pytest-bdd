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
    from typing import Tuple

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

    def step_docstring(self, value: Token) -> str:
        # TODO: Unescape escaped characters?
        [text] = value
        content = text[4:-3]
        dedented = textwrap.dedent(content)
        assert dedented[-1] == "\n"
        dedented_without_newline = dedented[:-1]
        return dedented_without_newline

    @v_args(inline=True)
    def step_arg(self, docstring, step_datatable) -> tuple[str, str]:
        return docstring, step_datatable

    def givens(self, steps: list[Tree]) -> tuple[str, list[Tree]]:
        return pytest_bdd_types.GIVEN, steps

    def whens(self, steps: list[Tree]) -> tuple[str, list[Tree]]:
        return pytest_bdd_types.WHEN, steps

    def thens(self, steps: list[Tree]) -> tuple[str, list[Tree]]:
        return pytest_bdd_types.THEN, steps

    @v_args(inline=True)
    def step(self, step_line: Token, step_arg: tuple = None):
        # TODO: step_arg not implemented yet
        return step_line, step_arg

    def steps(self, step_groups: list[tuple[str, list[Tree]]]) -> list[Step]:
        steps_data: list[tuple[str, tuple[Token, Token]]] = [
            (type, step_tree.children) for type, step_group in step_groups for step_tree, _ in step_group
        ]
        steps = [
            Step(
                name=str(value_token),
                type=bdd_type,
                line_number=type_token.line,
                indent=type_token.column,
                keyword=type_token + " ",
            )
            for bdd_type, [type_token, value_token] in steps_data
        ]
        return steps

    @v_args(inline=True)
    def scenario_line(self, _: Token, value: Token) -> Token:
        return value

    def tag_lines(self, value: list[Tree]) -> list[str]:
        tags = [el for tag_line in value for el in tag_line.children]
        return tags

    @v_args(inline=True)
    def scenario(
        self, tag_lines: list[str] | None, scenario_line: Token, steps: list[Step] | None, examples: Examples | None
    ):
        scenario = ScenarioTemplate(
            name=str(scenario_line),
            line_number=scenario_line.line,
            # example_converters=None,
            tags=tag_lines or [],
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

    def example_table(self, value: list[tuple[str]]) -> tuple[list[str], list[tuple[str]]]:
        header, rows = value[0], value[1:]
        # TODO: Validate lengths

        return header, rows

    @v_args(inline=True)
    def example_table_row(self, value: Token) -> list[str]:
        cells = split_line(value)
        return cells

    @v_args(inline=True)
    def examples(self, example_line: Tree, example_table: tuple[list[str], list[tuple[str]]]) -> Examples:
        examples_token, title = example_line.children
        ex = Examples()

        ex.line_number = examples_token.line
        ex.name = title
        header, rows = example_table
        ex.set_param_names(header)
        for row in rows:
            ex.add_example(row)
        return ex

    # def EXAMPLE_STRING(self, value):
    #     return value

    @v_args(inline=True)
    def feature(
        self,
        tag_lines: list[str] | None,
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
            tags=tag_lines or [],
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

    parsed = parse(content)
    parsed.filename = abs_filename
    parsed.rel_filename = rel_filename
    return parsed
