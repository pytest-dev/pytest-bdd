from __future__ import annotations

import collections
import enum
import os
from dataclasses import dataclass
from itertools import dropwhile
from typing import Callable, cast

import pyparsing as pp
from typing_extensions import Self

import pytest_bdd.parser

from .parser import ValidationError


def ungroup(expr: pp.ParserElement) -> pp.ParserElement:
    """Helper to undo pyparsing's default grouping of And expressions,
    even if all but one are non-empty.
    """

    def extractor(t: pp.ParseResults):
        [ex] = t
        return ex

    return pp.TokenConverter(expr).add_parse_action(extractor)


pp.enable_all_warnings()
# todo: make a context manager for this. both for grammar definition time and for parsing time
pp.ParserElement.set_default_whitespace_chars(" \t")


class ParseError(Exception):
    pass


class PStepType(enum.Enum):
    Given = "Given"
    When = "When"
    Then = "Then"
    And = "And"
    But = "But"


@dataclass
class PStepKeyword:
    type: PStepType
    keyword: str

    @classmethod
    def for_type(cls, type: PStepType) -> Callable[[pp.ParseResults], Self]:
        def from_tokens(tokens: pp.ParseResults) -> Self:
            keyword = tokens[0]
            return cls(type=type, keyword=keyword)

        return from_tokens


@dataclass
class PStep:
    type: PStepType
    name: str
    keyword: str

    @classmethod
    def from_tokens(cls, tokens: pp.ParseResults) -> Self:
        tokens = tokens.as_dict()
        keyword = cast(PStepKeyword, tokens["keyword"])

        return cls(type=keyword.type, name=tokens["name"], keyword=keyword.keyword)


@dataclass
class PStepGroup:
    steps: list[PStep]

    @classmethod
    def from_tokens(cls, tokens: pp.ParseResults) -> PStepGroup:
        tokens = tokens.as_dict()
        steps = cast(list[PStep], tokens["steps"])

        after_initial_givens = dropwhile(lambda step: step.type == "given", steps)
        for step in after_initial_givens:
            if step.type == "given":
                raise ParseError(f'Found a "given" step ({step.name!r}) after a "when" or "then" step.')

        return cls(steps=steps)


@dataclass
class PScenario:
    name: str
    steps: PStepGroup

    @classmethod
    def from_tokens(cls, tokens: pp.ParseResults) -> Self:
        d = tokens.as_dict()
        return cls(name=d["name"], steps=d["steps"])


@dataclass
class PScenarios:
    scenarios: list[PScenario]

    @classmethod
    def from_tokens(cls, tokens: pp.ParseResults) -> Self:
        scenarios = tokens.as_list()
        return cls(scenarios=scenarios)


@dataclass
class PFeature:
    name: str
    scenarios: PScenarios
    tags: list[str]

    @classmethod
    def from_tokens(cls, tokens: pp.ParseResults) -> Self:
        d = tokens.as_dict()
        [scenarios] = d["scenarios"]
        [tags] = d["tag_group"]
        return cls(name=d["name"], scenarios=scenarios, tags=tags["tag_lines_g"])


@dataclass
class PGherkinDocument:
    feature: PFeature

    @classmethod
    def from_tokens(cls, tokens: pp.ParseResults) -> Self:
        d = tokens.as_dict()
        [feature] = d["feature"]

        return cls(feature=feature)


GIVEN = pp.Keyword("Given")
WHEN = pp.Keyword("When")
THEN = pp.Keyword("Then")
AND = pp.Keyword("And")
BUT = pp.Keyword("But")

FEATURE = pp.one_of(["Feature", "Business Need", "Availability"])

SCENARIO = pp.one_of(["Scenario", "Example"])

GIVEN.set_parse_action(PStepKeyword.for_type(PStepType.Given))
WHEN.set_parse_action(PStepKeyword.for_type(PStepType.When))
THEN.set_parse_action(PStepKeyword.for_type(PStepType.Then))
AND.set_parse_action(PStepKeyword.for_type(PStepType.And))
BUT.set_parse_action(PStepKeyword.for_type(PStepType.But))

any_char = pp.Regex(r"[^\n]+").set_name("any_char")

step_kw = GIVEN | WHEN | THEN | AND | BUT


step = step_kw("keyword") + any_char("name") + pp.LineEnd()
step.set_name("step")
step.set_parse_action(PStep.from_tokens)

steps = step[1, ...]
steps.set_parse_action(PStepGroup.from_tokens)

scenario = SCENARIO + ":" + any_char("name") + pp.LineEnd() + steps("steps")
scenario.set_name("scenario")
scenario.set_parse_action(PScenario.from_tokens)

scenarios = scenario[0, ...]
scenarios.set_parse_action(PScenarios.from_tokens)

tag = pp.Combine("@" + pp.Word(pp.printables)("tag"))


@tag.set_parse_action
def _(tokens: pp.ParseResults) -> str:
    d = tokens.as_dict()
    return d["tag"]


# @dataclass()
# class TagLine:
#     tags: list[str]

tag_line = pp.LineStart() + pp.Group(tag[1, ...])("tags_g") + pp.LineEnd()


@tag_line.set_parse_action
def _(tokens: pp.ParseResults) -> list[str]:
    d = tokens.as_dict()
    # return d["tags_g"]
    return {"tags": d["tags_g"]}


tag_lines = pp.Group(tag_line[1, ...])("tag_lines_g")


@tag_lines.set_parse_action
def _(tokens: pp.ParseResults) -> list[str]:
    d = tokens.as_dict()
    v = {"tags": [tag for tag_line in d["tag_lines_g"] for tag in tag_line["tags"]]}
    return v


feature = (
    pp.Group(tag_lines)("tag_group*")
    + FEATURE
    + ":"
    + any_char("name")
    + pp.LineEnd()
    + pp.Group(scenarios)("scenarios")
)

feature.set_parse_action(PFeature.from_tokens)


# TODO: try to use ungroup(expr) and pp.Group instad of pp.And
gherkin_document = pp.And([pp.Group(feature)("feature")])
gherkin_document.set_parse_action(PGherkinDocument.from_tokens)

start = pp.And([pp.Group(gherkin_document)("gherkin_document")])

start.set_name("start")

start.create_diagram("/tmp/gherkin.html", show_results_names=True)

start.set_default_whitespace_chars(" \t")


input = """
Feature: My feature
    Scenario: My first scenario
        Given I have a step
        When I do something
        Then I should see something else
"""

# parsed = start.parse_string(input, parse_all=True)

# print(parsed)


def transform(tokens: pp.ParseResults):
    res = tokens.as_dict()

    [p_gherkin_doc] = cast(PGherkinDocument, res["gherkin_document"])
    p_feature = p_gherkin_doc.feature
    print(res)

    feature = pytest_bdd.parser.Feature(
        scenarios=collections.OrderedDict(),
        filename="",
        rel_filename="",
        name=None,
        tags=set(p_feature.tags),
        line_number=0,
        description="",
        background=None,
    )
    for p_scenario in p_feature.scenarios.scenarios:
        scenario = pytest_bdd.parser.ScenarioTemplate(
            feature=feature,
            name=p_scenario.name,
            line_number=0,
            templated=False,
        )
        feature.scenarios[scenario.name] = scenario

        for p_step in p_scenario.steps.steps:
            step = pytest_bdd.parser.Step(
                name=p_step.name,
                type=p_step.keyword,
                line_number=0,
                indent=0,
                keyword=p_step.keyword.strip(),
            )
            scenario.add_step(step)
    return feature


def parse(content: str):
    tokens = start.parse_string(content, parse_all=True)
    feature = transform(tokens)
    return feature


def parse_feature(basedir: str, filename: str, encoding="utf-8"):
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

    if feature.filename is None:
        raise ValidationError("Missing filename")
    if feature.rel_filename is None:
        raise ValidationError("Missing rel_filename")

    return feature


# document = transform(parsed)
#
# print(document)
#
#
# input = """
# Feature: lol
# Scenario: My first scenario
#     Given I have a step
#     When I do something
#     Then I should see something else
# Scenario: My second scenario
#     Given foo
# """
#
# parsed = start.parse_string(input, parse_all=True)
#
# print(parsed.as_dict())
