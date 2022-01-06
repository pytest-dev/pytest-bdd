import os.path
import re
import textwrap
import typing
from collections import OrderedDict
from itertools import chain, product
from typing import List, Type

import pytest
from attr import attrs, attrib, Factory

from . import exceptions, types

if typing.TYPE_CHECKING:
    from _pytest.mark import ParameterSet
SPLIT_LINE_RE = re.compile(r"(?<!\\)\|")
STEP_PARAM_RE = re.compile(r"<(.+?)>")
COMMENT_RE = re.compile(r"(^|(?<=\s))#")
STEP_PREFIXES = [
    ("Feature: ", types.FEATURE),
    ("Scenario Outline: ", types.SCENARIO_OUTLINE),
    ("Examples: Vertical", types.EXAMPLES_VERTICAL),
    ("Examples:", types.EXAMPLES),
    ("Scenario: ", types.SCENARIO),
    ("Background:", types.BACKGROUND),
    ("Given ", types.GIVEN),
    ("When ", types.WHEN),
    ("Then ", types.THEN),
    ("@", types.TAG),
    # Continuation of the previously mentioned step type
    ("And ", None),
    ("But ", None),
]


def split_line(line):
    """Split the given Examples line.

    :param str|unicode line: Feature file Examples line.

    :return: List of strings.
    """
    return [cell.replace("\\|", "|").strip() for cell in SPLIT_LINE_RE.split(line)[1:-1]]


def parse_line(line):
    """Parse step line to get the step prefix (Scenario, Given, When, Then or And) and the actual step name.

    :param line: Line of the Feature file.

    :return: `tuple` in form ("<prefix>", "<Line without the prefix>").
    """
    for prefix, _ in STEP_PREFIXES:
        if line.startswith(prefix):
            return prefix.strip(), line[len(prefix) :].strip()
    return "", line


def strip_comments(line):
    """Remove comments.

    :param str line: Line of the Feature file.

    :return: Stripped line.
    """
    res = COMMENT_RE.search(line)
    if res:
        line = line[: res.start()]
    return line.strip()


def get_step_type(line):
    """Detect step type by the beginning of the line.

    :param str line: Line of the Feature file.

    :return: SCENARIO, GIVEN, WHEN, THEN, or `None` if can't be detected.
    """
    for prefix, _type in STEP_PREFIXES:
        if line.startswith(prefix):
            return _type


def parse_feature(basedir: str, filename: str, encoding: str = "utf-8") -> "Feature":
    """Parse the feature file.

    :param str basedir: Feature files base directory.
    :param str filename: Relative path to the feature file.
    :param str encoding: Feature file encoding (utf-8 by default).
    """
    abs_filename = os.path.abspath(os.path.join(basedir, filename))
    rel_filename = os.path.join(os.path.basename(basedir), filename)
    feature = Feature(
        scenarios=OrderedDict(),
        filename=abs_filename,
        rel_filename=rel_filename,
        line_number=1,
        name=None,
        tags=set(),
        examples=Examples(),
        background=None,
        description="",
    )
    scenario: typing.Optional[ScenarioTemplate] = None
    mode = None
    prev_mode = None
    description: typing.List[str] = []
    step = None
    multiline_step = False
    prev_line = None

    with open(abs_filename, encoding=encoding) as f:
        content = f.read()

    for line_number, line in enumerate(content.splitlines(), start=1):
        unindented_line = line.lstrip()
        line_indent = len(line) - len(unindented_line)
        if step and (step.indent < line_indent or ((not unindented_line) and multiline_step)):
            multiline_step = True
            # multiline step, so just add line and continue
            step.add_line(line)
            continue
        else:
            step = None
            multiline_step = False
        stripped_line = line.strip()
        clean_line = strip_comments(line)
        if not clean_line and (not prev_mode or prev_mode not in types.FEATURE):
            continue
        mode = get_step_type(clean_line) or mode

        allowed_prev_mode = (types.BACKGROUND, types.GIVEN, types.WHEN)

        if not scenario and prev_mode not in allowed_prev_mode and mode in types.STEP_TYPES:
            raise exceptions.FeatureError(
                "Step definition outside of a Scenario or a Background", line_number, clean_line, filename
            )

        if mode == types.FEATURE:
            if prev_mode is None or prev_mode == types.TAG:
                _, feature.name = parse_line(clean_line)
                feature.line_number = line_number
                feature.tags = get_tags(prev_line)
            elif prev_mode == types.FEATURE:
                description.append(clean_line)
            else:
                raise exceptions.FeatureError(
                    "Multiple features are not allowed in a single feature file",
                    line_number,
                    clean_line,
                    filename,
                )

        prev_mode = mode

        # Remove Feature, Given, When, Then, And
        keyword, parsed_line = parse_line(clean_line)
        if mode in [types.SCENARIO, types.SCENARIO_OUTLINE]:
            tags = get_tags(prev_line)
            feature.scenarios[parsed_line] = scenario = ScenarioTemplate(
                feature=feature, name=parsed_line, line_number=line_number, tags=tags
            )
        elif mode == types.BACKGROUND:
            feature.background = Background(feature=feature, line_number=line_number)
        elif mode == types.EXAMPLES:
            mode = types.EXAMPLES_HEADERS
            _, example_table_name = parse_line(clean_line)
            obj = scenario or feature
            obj.examples.add_example_table(ExampleTableColumns)
            obj.examples.last_example_table.name = example_table_name or None
            obj.examples.last_example_table.line_number = line_number
        elif mode == types.EXAMPLES_VERTICAL:  # Deprecated; Has to be removed in future versions
            mode = types.EXAMPLE_LINE_VERTICAL
            _, example_table_name = parse_line(clean_line)
            obj = scenario or feature
            obj.examples.add_example_table(ExampleTableRows)
            obj.examples.last_example_table.name = example_table_name or None
            obj.examples.last_example_table.line_number = line_number
        elif mode == types.EXAMPLES_HEADERS:
            (scenario or feature).examples.last_example_table.example_params = [l for l in split_line(parsed_line) if l]
            mode = types.EXAMPLE_LINE
        elif mode == types.EXAMPLE_LINE:
            example_table: ExampleTableColumns = (scenario or feature).examples.last_example_table
            example_table.examples += [list(split_line(stripped_line))]
        elif mode == types.EXAMPLE_LINE_VERTICAL:
            example_table: ExampleTableRows = (scenario or feature).examples.last_example_table
            try:
                param, *examples = split_line(stripped_line)
            except ValueError:
                pass
            else:
                try:
                    example_table.add_example_row(param, examples)
                except exceptions.ExamplesNotValidError as exc:
                    if scenario:
                        raise exceptions.FeatureError(
                            f"Scenario has not valid examples. {exc.args[0]}",
                            line_number,
                            clean_line,
                            filename,
                        )
                    else:
                        raise exceptions.FeatureError(
                            f"Feature has not valid examples. {exc.args[0]}",
                            line_number,
                            clean_line,
                            filename,
                        )
        elif mode and mode not in (types.FEATURE, types.TAG):
            step = Step(name=parsed_line, type=mode, indent=line_indent, line_number=line_number, keyword=keyword)
            if feature.background and not scenario:
                target = feature.background
            else:
                target = scenario
            target.add_step(step)
        prev_line = clean_line

    feature.description = "\n".join(description).strip()
    return feature


class Feature:
    """Feature."""

    def __init__(self, scenarios, filename, rel_filename, name, tags, examples, background, line_number, description):
        self.scenarios: typing.Dict[str, ScenarioTemplate] = scenarios
        self.rel_filename = rel_filename
        self.filename = filename
        self.tags = tags
        self.examples = examples
        self.name = name
        self.line_number = line_number
        self.description = description
        self.background = background


class ScenarioTemplate:
    """A scenario template.

    Created when parsing the feature file, it will then be combined with the examples to create a Scenario."""

    def __init__(self, feature: Feature, name: str, line_number: int, tags=None):
        """

        :param str name: Scenario name.
        :param int line_number: Scenario line number.
        :param set tags: Set of tags.
        """
        self.feature = feature
        self.name = name
        self._steps: typing.List[Step] = []
        self.examples = Examples()
        self.line_number = line_number
        self.tags = tags or set()

    def add_step(self, step):
        """Add step to the scenario.

        :param pytest_bdd.parser.Step step: Step.
        """
        step.scenario = self
        self._steps.append(step)

    @property
    def steps(self):
        background = self.feature.background
        return (background.steps if background else []) + self._steps

    def render(self, context: typing.Mapping[str, typing.Any]) -> "Scenario":
        steps = [
            Step(
                name=templated_step.render(context),
                type=templated_step.type,
                indent=templated_step.indent,
                line_number=templated_step.line_number,
                keyword=templated_step.keyword,
            )
            for templated_step in self.steps
        ]
        return Scenario(feature=self.feature, name=self.name, line_number=self.line_number, steps=steps, tags=self.tags)

    @property
    def example_parametrizations(self) -> "typing.Optional[typing.List[ParameterSet]]":
        feature_scenario_examples_combinations = product(self.feature.examples, self.examples)

        def examples():
            for feature_examples, scenario_examples in feature_scenario_examples_combinations:
                common_param_names = set(feature_examples.keys()).intersection(scenario_examples.keys())
                if all(
                    feature_examples[param_name] == scenario_examples[param_name] for param_name in common_param_names
                ):
                    result = {**feature_examples, **scenario_examples}
                    if result != {}:
                        yield result

        return [pytest.param(example, id="-".join(example.values())) for example in examples()]

    def validate(self):
        """Validate the scenario.

        :raises ScenarioValidationError: when scenario is not valid
        """
        params = frozenset(sum((list(step.params) for step in self.steps), []))
        example_params = set(self.examples.example_params).union(self.feature.examples.example_params)
        if params and example_params and params != example_params:
            raise exceptions.ScenarioExamplesNotValidError(
                """Scenario "{}" in the feature "{}" has not valid examples. """
                """Set of step parameters {} should match set of example values {}.""".format(
                    self.name, self.feature.filename, sorted(params), sorted(example_params)
                )
            )


class Scenario:

    """Scenario."""

    def __init__(self, feature: Feature, name: str, line_number: int, steps: "typing.List[Step]", tags=None):
        """Scenario constructor.

        :param pytest_bdd.parser.Feature feature: Feature.
        :param str name: Scenario name.
        :param int line_number: Scenario line number.
        :param set tags: Set of tags.
        """
        self.feature = feature
        self.name = name
        self.steps = steps
        self.line_number = line_number
        self.tags = tags or set()
        self.failed = False


class Step:

    """Step."""

    def __init__(self, name, type, indent, line_number, keyword):
        """Step constructor.

        :param str name: step name.
        :param str type: step type.
        :param int indent: step text indent.
        :param int line_number: line number.
        :param str keyword: step keyword.
        """
        self.name = name
        self.keyword = keyword
        self.lines = []
        self.indent = indent
        self.type = type
        self.line_number = line_number
        self.failed = False
        self.start = 0
        self.stop = 0
        self.scenario = None
        self.background = None

    def add_line(self, line):
        """Add line to the multiple step.

        :param str line: Line of text - the continuation of the step name.
        """
        self.lines.append(line)

    @property
    def name(self):
        """Get step name."""
        multilines_content = textwrap.dedent("\n".join(self.lines)) if self.lines else ""

        # Remove the multiline quotes, if present.
        multilines_content = re.sub(
            pattern=r'^"""\n(?P<content>.*)\n"""$',
            repl=r"\g<content>",
            string=multilines_content,
            flags=re.DOTALL,  # Needed to make the "." match also new lines
        )

        lines = [self._name] + [multilines_content]
        return "\n".join(lines).strip()

    @name.setter
    def name(self, value):
        """Set step name."""
        self._name = value

    def __str__(self):
        """Full step name including the type."""
        return f'{self.type.capitalize()} "{self.name}"'

    @property
    def params(self):
        """Get step params."""
        return tuple(frozenset(STEP_PARAM_RE.findall(self.name)))

    def render(self, context: typing.Mapping[str, typing.Any]):
        def replacer(m: typing.Match):
            varname = m.group(1)
            return str(context[varname])

        return STEP_PARAM_RE.sub(replacer, self.name)


class Background:

    """Background."""

    def __init__(self, feature, line_number):
        """Background constructor.

        :param pytest_bdd.parser.Feature feature: Feature.
        :param int line_number: Line number.
        """
        self.feature = feature
        self.line_number = line_number
        self.steps = []

    def add_step(self, step):
        """Add step to the background."""
        step.background = self
        self.steps.append(step)


@attrs
class Examples:
    example_tables: List["ExampleTable"] = attrib(default=Factory(list))

    def add_example_table(self, builder: Type["ExampleTable"]):
        self.example_tables.append(builder())

    @property
    def last_example_table(self) -> "ExampleTable":
        return self.example_tables[-1]

    def __iter__(self) -> typing.Iterable[typing.Dict[str, typing.Any]]:
        if any(self.example_tables):
            yield from chain.from_iterable(self.example_tables)
        else:
            # We must make sure that we always have at least one element, otherwise
            # examples cartesian product will be empty
            yield {}

    @property
    def example_params(self):
        return set(chain.from_iterable(set(table.example_params) for table in self.example_tables))


@attrs
class ExampleTable:
    """Example table."""

    examples: list
    example_params = attrib(default=Factory(list))

    line_number = attrib(default=None)
    name = attrib(default=None)
    tags = attrib(default=Factory(list))

    def __iter__(self) -> typing.Iterable[typing.Dict[str, typing.Any]]:
        examples = self.examples
        for example in examples:
            assert len(self.example_params) == len(example)
            yield dict(zip(self.example_params, example))

    def __bool__(self):
        """Bool comparison."""
        return bool(self.examples)


@attrs
class ExampleTableRows(ExampleTable):
    example_param_values = attrib(default=Factory(list))

    def add_example_row(self, param, values):
        """Add example row.

        :param param: `str` parameter name
        :param values: `list` of `string` parameter values
        """
        if param in self.example_params:
            raise exceptions.ExamplesNotValidError(
                f"""Example rows should contain unique parameters. "{param}" appeared more than once"""
            )
        self.example_params.append(param)
        self.example_param_values.append(values)

    @property
    def examples(self):
        return list(zip(*self.example_param_values))


@attrs
class ExampleTableColumns(ExampleTable):
    examples = attrib(default=Factory(list))


def get_tags(line):
    """Get tags out of the given line.

    :param str line: Feature file text line.

    :return: List of tags.
    """
    if not line or not line.strip().startswith("@"):
        return set()
    return {tag.lstrip("@") for tag in line.strip().split(" @") if len(tag) > 1}
