from __future__ import annotations

import functools
import os.path
import re
import textwrap
from collections import OrderedDict

from tatsu.ast import AST

from pytest_bdd import types as bdd_types

from ._tatsu_parser import GherkinParser
from ._tatsu_parser import GherkinSemantics as _GherkinSemantics
from .parser import Background, Docstring, Examples, Feature, ScenarioTemplate, Step, ValidationError, split_line

parser = GherkinParser()


def get_column(node: AST) -> int:
    return node.parseinfo.tokenizer.line_info(node.parseinfo.pos).col


class GherkinSemantics(_GherkinSemantics):
    def feature(self, ast):
        feature_line = ast["feature_line"]
        tags = ast["tags"]
        description = textwrap.dedent(ast["description"] or "").strip()
        background = ast["background"]
        feature = Feature(
            scenarios=OrderedDict(),
            filename=None,
            rel_filename=None,
            name=str(feature_line["feature_name"]),
            tags=set(tags) if tags else set(),
            background=None,
            line_number=feature_line.parseinfo.line + 1,
            description=description or "",
        )
        if ast["scenarios"] is not None:
            for scenario in ast["scenarios"]:
                scenario.feature = feature
                feature.scenarios[scenario.name] = scenario

        if background is not None:
            background.feature = feature
            feature.background = background

        return feature

    def bg_scenarios(self, ast):  # noqa
        return ast

    def description(self, ast):  # noqa
        return "".join([line_part for line_parts in ast["lines"] for line_part in line_parts])

    def tag_lines(self, ast):
        tags = ast["tag"]
        assert all(tag.startswith("@") for tag in tags)
        tags = [tag[1:] for tag in tags]
        return tags

    def background(self, ast):  # noqa
        b = Background(feature=None, line_number=ast.parseinfo.line + 1)
        steps = ast["steps"] or []
        for step in steps:
            b.add_step(step)
        return b

    def scenarios(self, ast):  # noqa
        return ast

    def scenario(self, ast):  # noqa
        scenario = ScenarioTemplate(
            name=ast["scenario_name"],
            line_number=ast.parseinfo.line + 1,
            tags=set(ast["tags"]) if ast["tags"] else set(),
            feature=None,  # added later
            examples=ast["examples"],
        )
        assert isinstance(ast["steps"], list) or ast["steps"] is None
        for step in ast["steps"] or []:
            scenario.add_step(step)
        return scenario

    def step_def(self, ast):  # noqa
        def step_maker(bdd_type: str, keyword: str, column: int) -> Step:
            return Step(
                name=str(ast["name"]),
                type=bdd_type,
                line_number=ast.parseinfo.line + 1,
                indent=column,
                keyword=str(keyword.strip()),
                docstring=ast["docstring"],
                datatable=ast["table"],
            )

        return step_maker

    def steps_section(self, ast):  # noqa
        return (ast["plain_steps"] if ast["plain_steps"] else []) + [
            step for step_group in ast["nested_steps"] for step in step_group
        ]

    def step(self, ast, keyword):
        return ast

    def given_step(self, ast):  # noqa
        return functools.partial(ast["step_def"], keyword=ast["keyword"], column=get_column(ast) + 1)

    def when_step(self, ast):  # noqa
        return functools.partial(ast["step_def"], keyword=ast["keyword"], column=get_column(ast) + 1)

    def then_step(self, ast):  # noqa
        return functools.partial(ast["step_def"], keyword=ast["keyword"], column=get_column(ast) + 1)

    def and_step(self, ast):  # noqa
        return functools.partial(ast["step_def"], keyword=ast["keyword"], column=get_column(ast) + 1)

    def but_step(self, ast):  # noqa
        return functools.partial(ast["step_def"], keyword=ast["keyword"], column=get_column(ast) + 1)

    def given_steps(self, ast):  # noqa
        return [step_maker(bdd_type=bdd_types.GIVEN) for step_maker in ast["steps"]]

    def when_steps(self, ast):  # noqa
        return [step_maker(bdd_type=bdd_types.WHEN) for step_maker in ast["steps"]]

    def then_steps(self, ast):  # noqa
        return [step_maker(bdd_type=bdd_types.THEN) for step_maker in ast["steps"]]

    def examples(self, ast):
        table = ast["table"]
        ex = Examples(
            line_number=ast.parseinfo.line + 1,
            name=ast["name"],
        )

        header, rows = table[0], table[1:]
        ex.set_param_names(header)
        for row in rows:
            ex.add_example(row)
        return ex

    def example_line(self, ast):  # noqa
        return ast

    def table(self, ast):
        return ast["rows"]

    def table_row(self, ast):  # noqa
        cells = ast["cells"]
        cells = split_line(cells)
        return cells

    def EXAMPLE_TABLE_ROW(self, ast):  # noqa
        return ast

    def step_docstring(self, ast):  # noqa
        quotes, content_type, body = ast["container"]

        if not content_type:
            content_type = None

        # Dedent the lines of the body by the amount of indentation of the first triple quotes,
        # as per gherkin specification.

        quotes_indent = get_column(ast)

        lines = body.split("\n")
        sub_re = re.compile(rf"^[\t ]{{{quotes_indent}}}")

        dedented_lines = [sub_re.sub("", l) for l in lines]

        dedented = "\n".join(dedented_lines)
        return Docstring(dedented, content_type=content_type)

    def STEP_DOCSTRING_INNER(self, ast):  # noqa
        return ast

    def string(self, ast):  # noqa
        return ast

    def EXAMPLES(self, ast):  # noqa
        return ast

    def SCENARIOS(self, ast):  # noqa
        return ast

    def BACKGROUND(self, ast):  # noqa
        return ast

    def SCENARIO(self, ast):  # noqa
        return ast

    def SCENARIO_OUTLINE(self, ast):  # noqa
        return ast

    def SCENARIO_TEMPLATE(self, ast):  # noqa
        return ast

    def FEATURE(self, ast):  # noqa
        return ast

    def GIVEN(self, ast):  # noqa
        return ast

    def WHEN(self, ast):  # noqa
        return ast

    def THEN(self, ast):  # noqa
        return ast

    def AND(self, ast):  # noqa
        return ast

    def BUT(self, ast):  # noqa
        return ast

    def EXAMPLES_ALTS(self, ast):  # noqa
        return ast

    def SCENARIO_OUTLINE_ALTS(self, ast):  # noqa
        return ast

    def _NL(self, ast):  # noqa
        return ast


feat = """
Feature: feature name
    a b
    c d
    Background: hi
    Scenario: Scenario   name
    Scenario: Another scenario
    Scenario:nospace  #comment
"""


def main():
    import json
    import pprint

    from tatsu import parse
    from tatsu.util import asjson

    ast = parser.parse(feat, semantics=GherkinSemantics(), trace=True, colorize=True)
    # print('PPRINT')
    pprint.pprint(ast, indent=2, width=20)
    # print()

    # print('JSON')
    # print(json.dumps(asjson(ast), indent=2))
    # print()


# main()


def parse(content: str, filename: str | None = None) -> Feature:
    # tree = parser.parse(content)
    # pprint.pprint(tree, indent=2, width=20)

    feature = parser.parse(content, semantics=GherkinSemantics(), trace=True, colorize=True)

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
