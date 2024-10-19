from __future__ import annotations

import os.path
import re
import textwrap
from collections import OrderedDict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any

from .exceptions import StepError
from .gherkin_parser import Child, DataTable
from .gherkin_parser import Feature as GherkinFeature
from .gherkin_parser import GherkinDocument, Rule
from .gherkin_parser import Scenario as GherkinScenario
from .gherkin_parser import Step as GherkinStep
from .gherkin_parser import Tag as GherkinTag
from .gherkin_parser import get_gherkin_document
from .types import STEP_TYPES

STEP_PARAM_RE = re.compile(r"<(.+?)>")


@dataclass(eq=False)
class Feature:
    """Represents a feature parsed from a feature file.

    Attributes:
        scenarios (OrderedDict[str, ScenarioTemplate]): A dictionary of scenarios in the feature.
        filename (str): The absolute path of the feature file.
        rel_filename (str): The relative path of the feature file.
        name (Optional[str]): The name of the feature.
        tags (set[str]): A set of tags associated with the feature.
        line_number (int): The line number where the feature starts in the file.
        description (str): The description of the feature.
        background_steps (list[Step]): The background steps for the feature, if any.
    """

    scenarios: OrderedDict[str, ScenarioTemplate]
    filename: str
    rel_filename: str
    keyword: str
    name: str | None
    tags: set[str]
    line_number: int
    description: str
    background_steps: list[Step] = field(default_factory=list)


@dataclass(eq=False)
class Examples:
    """Represents examples used in scenarios for parameterization.

    Attributes:
        line_number (Optional[int]): The line number where the examples start.
        name (Optional[str]): The name of the examples.
        example_params (List[str]): The names of the parameters for the examples.
        examples (List[Sequence[str]]): The list of example rows.
    """

    line_number: int | None = None
    name: str | None = None
    example_params: list[str] = field(default_factory=list)
    examples: list[Sequence[str]] = field(default_factory=list)

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

    def as_contexts(self) -> Iterable[dict[str, Any]]:
        """Generate contexts for the examples.

        Yields:
            Dict[str, Any]: A dictionary mapping parameter names to their values for each example row.
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
class ScenarioTemplate:
    """Represents a scenario template within a feature.

    Attributes:
        feature (Feature): The feature to which this scenario belongs.
        keyword (str): The keyword used to define the scenario.
        name (str): The name of the scenario.
        line_number (int): The line number where the scenario starts in the file.
        templated (bool): Whether the scenario is templated.
        description (Optional[str]): The description of the scenario.
        tags (set[str]): A set of tags associated with the scenario.
        _steps (List[Step]): The list of steps in the scenario (internal use only).
        examples (Optional[Examples]): The examples used for parameterization in the scenario.
        rule (Optional[Rule]): The rule associated with the scenario
    """

    feature: Feature
    keyword: str
    name: str
    line_number: int
    templated: bool
    description: str | None = None
    tags: set[str] = field(default_factory=set)
    _steps: list[Step] = field(init=False, default_factory=list)
    examples: Examples | None = field(default_factory=Examples)
    rule: Rule | None = None

    def add_step(self, step: Step) -> None:
        """Add a step to the scenario.

        Args:
            step (Step): The step to add.
        """
        step.scenario = self
        self._steps.append(step)

    def get_background_steps(self):
        return self.feature.background_steps

    def get_rule_steps(self):
        """Get the background steps from the rule if any."""
        if not self.rule:
            return []
        # Ensure we collect steps from any children that have background
        return [child.background.steps for child in self.rule.children if child.background]

    @property
    def steps(self) -> list[Step]:
        """Get all steps for the scenario, including background steps from the feature and rule.

        Returns:
            List[Step]: A list of steps, including any background steps from the feature and rule.
        """
        steps = []

        # Add background steps from the feature
        steps.extend(self.get_background_steps())
        # Add background steps from the rule
        rule_steps = self.get_rule_steps()
        for rule_step in rule_steps:
            steps.extend(rule_step)
        # Add the scenario's own steps
        steps.extend(self._steps)

        return steps

    def render(self, context: Mapping[str, Any]) -> Scenario:
        """Render the scenario with the given context.

        Args:
            context (Mapping[str, Any]): The context for rendering steps.

        Returns:
            Scenario: A Scenario object with steps rendered based on the context.
        """
        scenario_steps = [
            Step(
                name=step.render(context),
                type=step.type,
                indent=step.indent,
                line_number=step.line_number,
                keyword=step.keyword,
                datatable=step.datatable,
                docstring=step.docstring,
                is_background=False,
            )
            for step in self._steps
        ]
        steps = []
        steps.extend(self.get_background_steps())
        steps.extend(self.get_rule_steps())
        steps.extend(scenario_steps)
        return Scenario(
            feature=self.feature,
            keyword=self.keyword,
            name=self.name,
            line_number=self.line_number,
            steps=steps,
            tags=self.tags,
            description=self.description,
        )


@dataclass(eq=False)
class Scenario:
    """Represents a scenario with steps.

    Attributes:
        feature (Feature): The feature to which this scenario belongs.
        keyword (str): The keyword used to define the scenario.
        name (str): The name of the scenario.
        line_number (int): The line number where the scenario starts in the file.
        steps (List[Step]): The list of steps in the scenario.
        description (Optional[str]): The description of the scenario.
        tags (set[str]): A set of tags associated with the scenario.
    """

    feature: Feature
    keyword: str
    name: str
    line_number: int
    steps: list[Step]
    description: str | None = None
    tags: set[str] = field(default_factory=set)


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
        scenario (Optional[ScenarioTemplate]): The scenario to which this step belongs (internal use only).
        is_background (bool): If the step is a background step (internal use only).
    """

    type: str
    name: str
    line_number: int
    indent: int
    keyword: str
    is_background: bool
    docstring: str | None = None
    datatable: DataTable | None = None
    failed: bool = field(init=False, default=False)
    scenario: ScenarioTemplate | None = field(init=False, default=None)

    def __init__(
        self,
        name: str,
        type: str,
        indent: int,
        line_number: int,
        keyword: str,
        is_background: bool,
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
        self.is_background = is_background

    def __str__(self) -> str:
        """Return a string representation of the step.

        Returns:
            str: A string representation of the step.
        """
        return f'{self.type.capitalize()} "{self.name}"'

    @property
    def params(self) -> tuple[str, ...]:
        """Get the parameters in the step name.

        Returns:
            Tuple[str, ...]: A tuple of parameter names found in the step name.
        """
        return tuple(frozenset(STEP_PARAM_RE.findall(self.name)))

    def render(self, context: Mapping[str, Any]) -> str:
        """Render the step name with the given context, but avoid replacing text inside angle brackets if context is missing.

        Args:
            context (Mapping[str, Any]): The context for rendering the step name.

        Returns:
            str: The rendered step name with parameters replaced only if they exist in the context.
        """

        def replacer(m: re.Match) -> str:
            varname = m.group(1)
            # If the context contains the variable, replace it. Otherwise, leave it unchanged.
            return str(context.get(varname, f"<{varname}>"))

        return STEP_PARAM_RE.sub(replacer, self.name)


class FeatureParser:
    """Converts a feature file into a Feature object.

    Args:
        basedir (str): The basedir for locating feature files.
        filename (str): The filename of the feature file.
        encoding (str): File encoding of the feature file to parse.
    """

    def __init__(self, basedir: str, filename: str, encoding: str = "utf-8"):
        self.abs_filename = os.path.abspath(os.path.join(basedir, filename))
        self.rel_filename = os.path.join(os.path.basename(basedir), filename)
        self.encoding = encoding

    @staticmethod
    def get_tag_names(tag_data: set[GherkinTag]) -> set[str]:
        """Extract tag names from tag data.

        Args:
            tag_data (List[dict]): The tag data to extract names from.

        Returns:
            set[str]: A set of tag names.
        """
        return {tag.name.lstrip("@") for tag in tag_data}

    def parse_steps(self, steps_data: list[GherkinStep], is_background: bool) -> list[Step]:
        """Parse a list of step data into Step objects.

        Args:
            steps_data (List[dict]): The list of step data.
            is_background (bool): If the step is a background step or not.

        Returns:
            List[Step]: A list of Step objects.
        """

        if not steps_data:
            return []

        first_step = steps_data[0]
        if first_step.keyword.lower() not in STEP_TYPES:
            raise StepError(
                message=f"First step in a scenario or background must start with 'Given', 'When' or 'Then', but got {first_step.keyword}.",
                line=first_step.location.line,
                line_content=first_step.text,
                filename=self.abs_filename,
            )

        steps = []
        current_type = first_step.keyword.lower()
        for step in steps_data:
            keyword = step.keyword.lower()
            if keyword in STEP_TYPES:
                current_type = keyword
            steps.append(
                Step(
                    name=step.text,
                    type=current_type,
                    indent=step.location.column - 1,
                    line_number=step.location.line,
                    keyword=step.keyword.title(),
                    datatable=step.datatable,
                    docstring=step.docstring.content if step.docstring else None,
                    is_background=is_background,
                )
            )
        return steps

    def parse_scenario(
        self, scenario_data: GherkinScenario, feature: Feature, rule: Rule | None = None
    ) -> ScenarioTemplate:
        """Parse a scenario into a ScenarioTemplate object.

        Args:
            scenario_data (GherkinScenario): The dictionary containing scenario data.
            feature (Feature): The feature to which this scenario belongs.
            rule (Optional[Rule]): Rule associated with the scenario.

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
            tags=self.get_tag_names(scenario_data.tags if rule is None else scenario_data.tags.union(rule.tags)),
            description=textwrap.dedent(scenario_data.description),
            rule=rule,
        )

        for step in self.parse_steps(scenario_data.steps, is_background=False):
            scenario.add_step(step)

        for example_data in scenario_data.examples:
            examples = Examples(
                line_number=example_data.location.line,
                name=example_data.name,
            )
            if example_data.table_header is not None:
                param_names = [cell.value for cell in example_data.table_header.cells]
                examples.set_param_names(param_names)
                if example_data.table_body is not None:
                    for row in example_data.table_body:
                        values = [cell.value or "" for cell in row.cells]
                        examples.add_example(values)
                    scenario.examples = examples

        return scenario

    def _parse_feature_file(self) -> GherkinDocument:
        """Parse a feature file into a Feature object.

        Returns:
            Dict: A Gherkin document representation of the feature file.
        """
        return get_gherkin_document(self.abs_filename, self.encoding)

    def parse(self) -> Feature:
        gherkin_doc: GherkinDocument = self._parse_feature_file()
        feature_data: GherkinFeature = gherkin_doc.feature
        feature = Feature(
            scenarios=OrderedDict(),
            keyword=feature_data.keyword,
            filename=self.abs_filename,
            rel_filename=self.rel_filename,
            name=feature_data.name,
            tags=self.get_tag_names(feature_data.tags),
            line_number=feature_data.location.line,
            description=textwrap.dedent(feature_data.description),
        )

        def parse_feature_data(children: list[Child], feature: Feature, current_rule: Rule | None = None):
            for child in children:
                # Check for rule
                if child.rule is not None:
                    current_rule = child.rule
                    parse_feature_data(current_rule.children, feature, current_rule)
                # Check for background
                elif child.background is not None:
                    feature.background_steps = self.parse_steps(child.background.steps, is_background=True)
                # Check for scenario
                elif child.scenario is not None:
                    scenario = self.parse_scenario(child.scenario, feature, current_rule)
                    feature.scenarios[scenario.name] = scenario

        parse_feature_data(feature_data.children, feature)

        return feature
