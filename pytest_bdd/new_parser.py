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
from pytest_bdd.parser import Examples, Feature, Scenario, ScenarioTemplate, Step

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
    def gherkin_document(self, value: Feature) -> Feature:
        return value

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
    def scenario_line(self, value: Token) -> Token:
        return value

    @v_args(inline=True)
    def scenario(self, scenario_line: Token, steps: list[Step] | None):
        scenario = ScenarioTemplate(
            name=str(scenario_line),
            line_number=scenario_line.line,
            # example_converters=None,
            tags=None,
            feature=None,  # added later
        )
        for step in steps or []:
            scenario.add_step(step)
        return scenario

    @v_args(inline=True)
    def tag(self, value):
        return value

    def feature(self, value: list[Tree]):
        try:
            feature_header = next(el for el in value if el.data == "feature_header")
            tag_lines = [el for el in feature_header.children if el.data == "tag_line"]
            tags = [el for tag_line in tag_lines for el in tag_line.children]
        except StopIteration:
            tags = []

        feature_line = next(el for el in value if el.data == "feature_line")
        scenarios = next(el for el in value if el.data == "scenarios")

        [feature_name] = feature_line.children

        feature = Feature(
            scenarios=OrderedDict(),
            filename=None,
            rel_filename=None,
            name=str(feature_name),
            tags=tags,
            background=None,
            line_number=feature_name.line,
            description=None,
        )
        for scenario in scenarios.children:
            scenario.feature = feature
            feature.scenarios[scenario.name] = scenario
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
