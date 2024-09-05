from __future__ import annotations

import linecache
import os.path
import re
import textwrap
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner

from .exceptions import FeatureError
from .types import GIVEN, THEN, WHEN

STEP_PARAM_RE = re.compile(r"<(.+?)>")
COMMENT_RE = re.compile(r"(^|(?<=\s))#")


def strip_comments(line: str) -> str:
    """Remove comments from a line of text."""
    if res := COMMENT_RE.search(line):
        line = line[: res.start()]
    return line.strip()


def parse_feature(basedir: str, filename: str, encoding: str = "utf-8") -> Feature:
    """Parse a feature file into a Feature object."""
    abs_filename = os.path.abspath(os.path.join(basedir, filename))
    rel_filename = os.path.join(os.path.basename(basedir), filename)
    with open(abs_filename, encoding=encoding) as f:
        file_contents = f.read()
    try:
        gherkin_document = Parser().parse(TokenScanner(file_contents))
    except CompositeParserException as e:
        raise FeatureError(
            e.args[0],
            e.errors[0].location["line"],
            linecache.getline(abs_filename, e.errors[0].location["line"]).rstrip("\n"),
            abs_filename,
        ) from e
    return dict_to_feature(abs_filename, rel_filename, gherkin_document)


@dataclass(eq=False)
class Feature:
    scenarios: OrderedDict[str, ScenarioTemplate]
    filename: str
    rel_filename: str
    name: str | None
    tags: set[str]
    background: Background | None
    line_number: int
    description: str


@dataclass(eq=False)
class Examples:
    line_number: int | None = None
    name: str | None = None
    example_params: list[str] = field(default_factory=list)
    examples: list[Sequence[str]] = field(default_factory=list)

    def set_param_names(self, keys: Iterable[str]) -> None:
        self.example_params = [str(key) for key in keys]

    def add_example(self, values: Sequence[str]) -> None:
        self.examples.append([str(value) if value is not None else "" for value in values])

    def as_contexts(self) -> Iterable[dict[str, Any]]:
        for row in self.examples:
            assert len(self.example_params) == len(row)
            yield dict(zip(self.example_params, row))

    def __bool__(self) -> bool:
        return bool(self.examples)


@dataclass(eq=False)
class ScenarioTemplate:
    feature: Feature
    name: str
    line_number: int
    templated: bool
    description: str | None = None
    tags: set[str] = field(default_factory=set)
    _steps: list[Step] = field(init=False, default_factory=list)
    examples: Examples | None = field(default_factory=Examples)

    def add_step(self, step: Step) -> None:
        step.scenario = self
        self._steps.append(step)

    @property
    def steps(self) -> list[Step]:
        return (self.feature.background.steps if self.feature.background else []) + self._steps

    def render(self, context: Mapping[str, Any]) -> Scenario:
        background_steps = self.feature.background.steps if self.feature.background else []
        scenario_steps = [
            Step(
                name=step.render(context),
                type=step.type,
                indent=step.indent,
                line_number=step.line_number,
                keyword=step.keyword,
            )
            for step in self._steps
        ]
        steps = background_steps + scenario_steps
        return Scenario(
            feature=self.feature,
            name=self.name,
            line_number=self.line_number,
            steps=steps,
            tags=self.tags,
            description=self.description,
        )


@dataclass(eq=False)
class Scenario:
    feature: Feature
    name: str
    line_number: int
    steps: list[Step]
    description: str | None = None
    tags: set[str] = field(default_factory=set)


@dataclass(eq=False)
class Step:
    type: str
    _name: str
    line_number: int
    indent: int
    keyword: str
    failed: bool = field(init=False, default=False)
    scenario: ScenarioTemplate | None = field(init=False, default=None)
    background: Background | None = field(init=False, default=None)
    lines: list[str] = field(init=False, default_factory=list)

    def __init__(self, name: str, type: str, indent: int, line_number: int, keyword: str) -> None:
        self.name = name
        self.type = type
        self.indent = indent
        self.line_number = line_number
        self.keyword = keyword

    def __str__(self) -> str:
        return f'{self.type.capitalize()} "{self.name}"'

    @property
    def params(self) -> tuple[str, ...]:
        return tuple(frozenset(STEP_PARAM_RE.findall(self.name)))

    def render(self, context: Mapping[str, Any]) -> str:
        def replacer(m: re.Match) -> str:
            varname = m.group(1)
            return str(context.get(varname, f"<missing:{varname}>"))

        return STEP_PARAM_RE.sub(replacer, self.name)


@dataclass(eq=False)
class Background:
    feature: Feature
    line_number: int
    steps: list[Step] = field(init=False, default_factory=list)

    def add_step(self, step: Step) -> None:
        step.background = self
        self.steps.append(step)


def dict_to_feature(abs_filename: str, rel_filename: str, data: dict) -> Feature:
    def get_tag_names(tag_data: list[dict]) -> set[str]:
        return {tag["name"].lstrip("@") for tag in tag_data}

    def get_step_type(keyword: str) -> str | None:
        return {
            "given": GIVEN,
            "when": WHEN,
            "then": THEN,
        }.get(keyword)

    def parse_steps(steps_data: list[dict]) -> list[Step]:
        steps = []
        current_step_type = None
        for step_data in steps_data:
            keyword = step_data["keyword"].strip().lower()
            current_step_type = get_step_type(keyword) or current_step_type
            name = strip_comments(step_data["text"])
            if "docString" in step_data:
                doc_string = textwrap.dedent(step_data["docString"]["content"])
                name = f"{name}\n{doc_string}"
            steps.append(
                Step(
                    name=name,
                    type=current_step_type,
                    indent=step_data["location"]["column"] - 1,
                    line_number=step_data["location"]["line"],
                    keyword=keyword.title(),
                )
            )
        return steps

    def parse_scenario(scenario_data: dict, feature: Feature) -> ScenarioTemplate:
        scenario = ScenarioTemplate(
            feature=feature,
            name=strip_comments(scenario_data["name"]),
            line_number=scenario_data["location"]["line"],
            templated=False,
            tags=get_tag_names(scenario_data["tags"]),
            description=textwrap.dedent(scenario_data.get("description", "")),
        )
        for step in parse_steps(scenario_data["steps"]):
            scenario.add_step(step)

        if "examples" in scenario_data:
            for example_data in scenario_data["examples"]:
                examples = Examples(
                    line_number=example_data["location"]["line"],
                    name=example_data["name"],
                )
                param_names = [cell["value"] for cell in example_data["tableHeader"]["cells"]]
                examples.set_param_names(param_names)
                for row in example_data["tableBody"]:
                    values = [cell["value"] or "" for cell in row["cells"]]
                    examples.add_example(values)
                scenario.examples = examples

        return scenario

    def parse_background(background_data: dict, feature: Feature) -> Background:
        background = Background(
            feature=feature,
            line_number=background_data["location"]["line"],
        )
        background.steps = parse_steps(background_data["steps"])
        return background

    feature_data = data["feature"]
    feature = Feature(
        scenarios=OrderedDict(),
        filename=abs_filename,
        rel_filename=rel_filename,
        name=strip_comments(feature_data["name"]),
        tags=get_tag_names(feature_data["tags"]),
        background=None,
        line_number=feature_data["location"]["line"],
        description=textwrap.dedent(feature_data.get("description", "")),
    )

    for child in feature_data["children"]:
        if "background" in child:
            feature.background = parse_background(child["background"], feature)
        elif "scenario" in child:
            scenario = parse_scenario(child["scenario"], feature)
            feature.scenarios[scenario.name] = scenario

    return feature
