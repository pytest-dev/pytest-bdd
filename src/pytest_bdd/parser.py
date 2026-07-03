from __future__ import annotations

import copy
import os.path
import re
import textwrap
from collections import OrderedDict
from collections.abc import Generator, Iterable, Mapping, Sequence
from dataclasses import dataclass, field

from .exceptions import StepError
from .gherkin_parser import Background as GherkinBackground
from .gherkin_parser import DataTable, GherkinDocument, get_gherkin_document
from .gherkin_parser import Feature as GherkinFeature
from .gherkin_parser import Rule as GherkinRule
from .gherkin_parser import Scenario as GherkinScenario
from .gherkin_parser import Step as GherkinStep
from .gherkin_parser import Tag as GherkinTag
from .types import STEP_TYPE_BY_PARSER_KEYWORD

PARAM_RE = re.compile(r"<(.+?)>")


def render_string(input_string: str, render_context: Mapping[str, object]) -> str:
    """
    Render the string with the given context,
    but avoid replacing text inside angle brackets if context is missing.

    Args:
        input_string (str): The string for which to render/replace params.
        render_context (Mapping[str, object]): The context for rendering the string.

    Returns:
        str: The rendered string with parameters replaced only if they exist in the context.
    """

    def replacer(m: re.Match) -> str:
        varname = m.group(1)
        # If the context contains the variable, replace it. Otherwise, leave it unchanged.
        return str(render_context.get(varname, f"<{varname}>"))

    return PARAM_RE.sub(replacer, input_string)


def get_tag_names(tag_data: list[GherkinTag]) -> set[str]:
    """Extract tag names from tag data.

    Args:
        tag_data (list[dict]): The tag data to extract names from.

    Returns:
        set[str]: A set of tag names.
    """
    return {tag.name.lstrip("@") for tag in tag_data}


@dataclass(eq=False)
class Feature:
    """Represents a feature parsed from a feature file.

    Attributes:
        scenarios (OrderedDict[str, ScenarioTemplate]): A dictionary of scenarios in the feature.
        filename (str): The absolute path of the feature file.
        rel_filename (str): The relative path of the feature file.
        name (str): The name of the feature.
        tags (set[str]): A set of tags associated with the feature.
        background (Background | None): The background steps for the feature, if any.
        line_number (int): The line number where the feature starts in the file.
        description (str): The description of the feature.
    """

    scenarios: OrderedDict[str, ScenarioTemplate]
    filename: str
    rel_filename: str
    language: str
    keyword: str
    name: str
    tags: set[str]
    background: Background | None
    line_number: int
    description: str


@dataclass(eq=False)
class Examples:
    """Represents examples used in scenarios for parameterization.

    Attributes:
        line_number (int | None): The line number where the examples start.
        name (str | None): The name of the examples.
        example_params (list[str]): The names of the parameters for the examples.
        examples (list[Sequence[str]]): The list of example rows.
    """

    line_number: int | None = None
    name: str | None = None
    example_params: list[str] = field(default_factory=list)
    examples: list[Sequence[str]] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)

    def set_param_names(self, keys: Iterable[str]) -> None:
        """Set the parameter names for the examples.

        Args:
            keys (Iterable[str]): The parameter names to set.
        """
        self.example_params = [str(key) for key in keys]

    def add_example(self, values: Sequence[str]) -> None:
        """Add a new example row.

        Args:
            values (Sequence[str]): The values for the example row.
        """
        self.examples.append([str(value) if value is not None else "" for value in values])

    def as_contexts(self) -> Generator[dict[str, str]]:
        """Generate contexts for the examples.

        Yields:
            dict[str, str]: A dictionary mapping parameter names to their values for each example row.
        """
        for row in self.examples:
            assert len(self.example_params) == len(row)
            yield dict(zip(self.example_params, row))

    def __bool__(self) -> bool:
        """Check if there are any examples.

        Returns:
            bool: True if there are examples, False otherwise.
        """
        return bool(self.examples)


@dataclass(eq=False)
class Rule:
    keyword: str
    name: str
    description: str
    tags: set[str]
    background: Background | None = None


@dataclass(eq=False)
class ScenarioTemplate:
    """Represents a scenario template within a feature.

    Attributes:
        feature (Feature): The feature to which this scenario belongs.
        keyword (str): The keyword used to define the scenario.
        name (str): The name of the scenario.
        line_number (int): The line number where the scenario starts in the file.
        templated (bool): Whether the scenario is templated.
        description (str | None): The description of the scenario.
        tags (set[str]): A set of tags associated with the scenario.
        _steps (list[Step]): The list of steps in the scenario (internal use only).
        examples (Examples | None): The examples used for parameterization in the scenario.
        rule (Rule | None): The rule to which the scenario may belong (None = no rule).
    """

    feature: Feature
    keyword: str
    name: str
    line_number: int
    templated: bool
    description: str
    tags: set[str] = field(default_factory=set)
    _steps: list[Step] = field(init=False, default_factory=list)
    examples: list[Examples] = field(default_factory=list[Examples])
    rule: Rule | None = None

    def add_step(self, step: Step) -> None:
        """Add a step to the scenario.

        Args:
            step (Step): The step to add.
        """
        step.scenario = self
        self._steps.append(step)

    @property
    def all_background_steps(self) -> list[Step]:
        steps = []
        # Add background steps from the feature
        if self.feature.background:
            steps.extend(self.feature.background.steps)
        if self.rule is not None and self.rule.background is not None:
            # Add background steps from the rule
            steps.extend(self.rule.background.steps)
        return steps

    @property
    def steps(self) -> list[Step]:
        """Get all steps for the scenario, including background steps.

        Returns:
            list[Step]: A list of steps, including any background steps from the feature.
        """
        return self.all_background_steps + self._steps

    def render(self, context: Mapping[str, object]) -> Scenario:
        """Render the scenario with the given context.

        Args:
            context (Mapping[str, object]): The context for rendering steps.

        Returns:
            Scenario: A Scenario object with steps rendered based on the context.
        """
        base_steps = self.all_background_steps + self._steps
        scenario_steps = [
            Step(
                name=render_string(step.name, context),
                type=step.type,
                indent=step.indent,
                line_number=step.line_number,
                keyword=step.keyword,
                datatable=step.render_datatable(step.datatable, context) if step.datatable else None,
                docstring=render_string(step.docstring, context) if step.docstring else None,
            )
            for step in base_steps
        ]
        return Scenario(
            feature=self.feature,
            keyword=self.keyword,
            name=render_string(self.name, context),
            line_number=self.line_number,
            steps=scenario_steps,
            tags=self.tags,
            description=self.description,
            rule=self.rule,
        )


@dataclass(eq=False)
class Scenario:
    """Represents a scenario with steps.

    Attributes:
        feature (Feature): The feature to which this scenario belongs.
        keyword (str): The keyword used to define the scenario.
        name (str): The name of the scenario.
        line_number (int): The line number where the scenario starts in the file.
        steps (list[Step]): The list of steps in the scenario.
        description (str | None): The description of the scenario.
        tags (set[str]): A set of tags associated with the scenario.
    """

    feature: Feature
    keyword: str
    name: str
    line_number: int
    steps: list[Step]
    description: str
    tags: set[str] = field(default_factory=set)
    rule: Rule | None = None


@dataclass(eq=False)
class Step:
    """Represents a step within a scenario or background.

    Attributes:
        type (str): The type of step (e.g., 'given', 'when', 'then').
        name (str): The name of the step.
        line_number (int): The line number where the step starts in the file.
        indent (int): The indentation level of the step.
        keyword (str): The keyword used for the step (e.g., 'Given', 'When', 'Then').
        failed (bool): Whether the step has failed (internal use only).
        scenario (ScenarioTemplate | None): The scenario to which this step belongs (internal use only).
        background (Background | None): The background to which this step belongs (internal use only).
    """

    type: str
    name: str
    line_number: int
    indent: int
    keyword: str
    docstring: str | None = None
    datatable: DataTable | None = None
    failed: bool = field(init=False, default=False)
    scenario: ScenarioTemplate | None = field(init=False, default=None)
    background: Background | None = field(init=False, default=None)

    def __init__(
        self,
        name: str,
        type: str,
        indent: int,
        line_number: int,
        keyword: str,
        datatable: DataTable | None = None,
        docstring: str | None = None,
    ) -> None:
        """Initialize a step.

        Args:
            name (str): The name of the step.
            type (str): The type of the step (e.g., 'given', 'when', 'then').
            indent (int): The indentation level of the step.
            line_number (int): The line number where the step starts in the file.
            keyword (str): The keyword used for the step (e.g., 'Given', 'When', 'Then').
        """
        self.name = name
        self.type = type
        self.indent = indent
        self.line_number = line_number
        self.keyword = keyword
        self.datatable = datatable
        self.docstring = docstring

    def __str__(self) -> str:
        """Return a string representation of the step.

        Returns:
            str: A string representation of the step.
        """
        return f'{self.type.capitalize()} "{self.name}"'

    @staticmethod
    def render_datatable(datatable: DataTable, context: Mapping[str, object]) -> DataTable:
        """
        Render the datatable with the given context,
        but avoid replacing text inside angle brackets if context is missing.

        Args:
            datatable (DataTable): The datatable to render.
            context (Mapping[str, object]): The context for rendering the datatable.

        Returns:
            datatable (DataTable): The rendered datatable with parameters replaced only if they exist in the context.
        """
        rendered_datatable = copy.deepcopy(datatable)
        for row in rendered_datatable.rows:
            for cell in row.cells:
                cell.value = render_string(cell.value, context)
        return rendered_datatable


@dataclass(eq=False)
class Background:
    """Represents the background steps for a feature.

    Attributes:
        line_number (int): The line number where the background starts in the file.
        steps (list[Step]): The list of steps in the background.
    """

    line_number: int
    steps: list[Step] = field(init=False, default_factory=list)

    def add_step(self, step: Step) -> None:
        """Add a step to the background.

        Args:
            step (Step): The step to add.
        """
        step.background = self
        self.steps.append(step)


class FeatureParser:
    """Converts a feature file into a Feature object.

    Args:
        basedir (str): The basedir for locating feature files.
        filename (str): The filename of the feature file.
        encoding (str): File encoding of the feature file to parse.
    """

    def __init__(self, basedir: str, filename: str, encoding: str = "utf-8") -> None:
        self.abs_filename = os.path.abspath(os.path.join(basedir, filename))
        self.rel_filename = os.path.join(os.path.basename(basedir), filename)
        self.encoding = encoding

    def parse_steps(self, steps_data: list[GherkinStep]) -> list[Step]:
        """Parse a list of step data into Step objects.

        Args:
            steps_data (list[dict]): The list of step data.

        Returns:
            list[Step]: A list of Step objects.
        """

        if not steps_data:
            return []

        first_step = steps_data[0]
        if first_step.keyword_type not in STEP_TYPE_BY_PARSER_KEYWORD:
            raise StepError(
                message=f"First step in a scenario or background must start with 'Given', 'When' or 'Then', but got {first_step.keyword}.",
                line=first_step.location.line,
                line_content=first_step.text,
                filename=self.abs_filename,
            )

        steps = []
        current_type = STEP_TYPE_BY_PARSER_KEYWORD[first_step.keyword_type]
        for step in steps_data:
            current_type = STEP_TYPE_BY_PARSER_KEYWORD.get(step.keyword_type, current_type)
            steps.append(
                Step(
                    name=step.text,
                    type=current_type,
                    indent=step.location.column - 1,
                    line_number=step.location.line,
                    keyword=step.keyword.title(),
                    datatable=step.datatable,
                    docstring=step.docstring.content if step.docstring else None,
                )
            )
        return steps

    def parse_scenario(
        self, scenario_data: GherkinScenario, feature: Feature, rule: Rule | None = None
    ) -> ScenarioTemplate:
        """Parse a scenario data dictionary into a ScenarioTemplate object.

        Args:
            scenario_data (dict): The dictionary containing scenario data.
            feature (Feature): The feature to which this scenario belongs.
            rule (Rule | None): The rule to which this scenario may belong. (None = no rule)

        Returns:
            ScenarioTemplate: A ScenarioTemplate object representing the parsed scenario.
        """
        templated = bool(scenario_data.examples)
        scenario = ScenarioTemplate(
            feature=feature,
            keyword=scenario_data.keyword,
            name=scenario_data.name,
            line_number=scenario_data.location.line,
            templated=templated,
            tags=get_tag_names(scenario_data.tags),
            description=textwrap.dedent(scenario_data.description),
            rule=rule,
        )
        for step in self.parse_steps(scenario_data.steps):
            scenario.add_step(step)

        # Loop over multiple example tables if they exist
        for example_data in scenario_data.examples:
            examples = Examples(
                line_number=example_data.location.line,
                name=example_data.name,
                tags=get_tag_names(example_data.tags),
            )
            if example_data.table_header is not None:
                param_names = [cell.value for cell in example_data.table_header.cells]
                examples.set_param_names(param_names)
                if example_data.table_body is not None:
                    for row in example_data.table_body:
                        values = [cell.value or "" for cell in row.cells]
                        examples.add_example(values)
                scenario.examples.append(examples)

        return scenario

    def parse_background(self, background_data: GherkinBackground) -> Background:
        background = Background(
            line_number=background_data.location.line,
        )
        background.steps = self.parse_steps(background_data.steps)
        for step in background.steps:
            step.background = background
        return background

    def _parse_feature_file(self) -> GherkinDocument:
        """Parse a feature file into a Feature object.

        Returns:
            Dict: A Gherkin document representation of the feature file.
        """
        return get_gherkin_document(self.abs_filename, self.encoding)

    def parse(self) -> Feature:
        """Parse the feature file and return a Feature object with its backgrounds, rules, and scenarios."""
        gherkin_doc: GherkinDocument = self._parse_feature_file()
        feature_data: GherkinFeature = gherkin_doc.feature
        feature = Feature(
            scenarios=OrderedDict(),
            keyword=feature_data.keyword,
            filename=self.abs_filename,
            rel_filename=self.rel_filename,
            name=feature_data.name,
            tags=get_tag_names(feature_data.tags),
            background=None,
            line_number=feature_data.location.line,
            description=textwrap.dedent(feature_data.description),
            language=feature_data.language,
        )

        for child in feature_data.children:
            if child.background:
                feature.background = self.parse_background(child.background)
            elif child.rule:
                self._parse_and_add_rule(child.rule, feature)
            elif child.scenario:
                self._parse_and_add_scenario(child.scenario, feature)

        return feature

    def _parse_and_add_rule(self, rule_data: GherkinRule, feature: Feature) -> None:
        """Parse a rule, including its background and scenarios, and add to the feature."""
        background = self._extract_rule_background(rule_data)

        rule = Rule(
            keyword=rule_data.keyword,
            name=rule_data.name,
            description=rule_data.description,
            tags=get_tag_names(rule_data.tags),
            background=background,
        )

        for scenario in self._extract_rule_scenarios(rule_data, feature, rule):
            feature.scenarios[scenario.name] = scenario

    def _extract_rule_background(self, rule_data: GherkinRule) -> Background | None:
        """Extract the first background from rule children if it exists."""
        for child in rule_data.children:
            if child.background:
                return self.parse_background(child.background)
        return None

    def _extract_rule_scenarios(
        self, rule_data: GherkinRule, feature: Feature, rule: Rule
    ) -> Generator[ScenarioTemplate]:
        """Yield each parsed scenario under a rule."""
        for child in rule_data.children:
            if child.scenario:
                yield self.parse_scenario(child.scenario, feature, rule)

    def _parse_and_add_scenario(
        self, scenario_data: GherkinScenario, feature: Feature, rule: Rule | None = None
    ) -> None:
        """Parse an individual scenario and add it to the feature's scenarios."""
        scenario = self.parse_scenario(scenario_data, feature, rule)
        feature.scenarios[scenario.name] = scenario
