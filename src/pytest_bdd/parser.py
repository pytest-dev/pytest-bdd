import linecache
import re
import textwrap
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple, Union

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner
from pydantic import BaseModel, field_validator, model_validator

from . import exceptions
from .types import STEP_TYPES

STEP_PARAM_RE = re.compile(r"<(.+?)>")
COMMENT_RE = re.compile(r"(^|(?<=\s))#")


def check_instance_by_name(obj: Any, class_name: str) -> bool:
    return obj.__class__.__name__ == class_name


def strip_comments(line: str) -> str:
    """Remove comments from a line of text.

    Args:
        line (str): The line of text from which to remove comments.

    Returns:
        str: The line of text without comments, with leading and trailing whitespace removed.
    """
    if res := COMMENT_RE.search(line):
        line = line[: res.start()]
    return line.strip()


class Location(BaseModel):
    column: int
    line: int


class Comment(BaseModel):
    location: Location
    text: str


class Cell(BaseModel):
    location: Location
    value: str


class Row(BaseModel):
    id: str
    location: Location
    cells: List[Cell]


class DataTable(BaseModel):
    name: Optional[str] = None
    location: Location
    tableHeader: Optional[Row] = None
    tableBody: Optional[List[Row]] = None

    def as_contexts(self) -> Iterable[Dict[str, Any]]:
        """
        Generate contexts for the examples.

        Yields:
            Dict[str, Any]: A dictionary mapping parameter names to their values for each example row.
        """
        if not self.tableHeader or not self.tableBody:
            return  # If header or body is missing, there's nothing to yield

        # Extract parameter names from the tableHeader (row with headers)
        example_params = [cell.value for cell in self.tableHeader.cells]

        for row in self.tableBody:
            assert len(example_params) == len(row.cells), "Row length does not match header length"
            # Map parameter names (from header) to values (from the row)
            yield dict(zip(example_params, [cell.value for cell in row.cells]))


class DocString(BaseModel):
    content: str
    delimiter: str
    location: Location

    @field_validator("content", mode="before")
    def dedent_content(cls, value: str) -> str:
        return textwrap.dedent(value)


class Step(BaseModel):
    id: str
    keyword: str
    keywordType: str
    location: Location
    text: str
    dataTable: Optional[DataTable] = None
    docString: Optional[DocString] = None
    raw_name: Optional[str] = None
    name: Optional[str] = None
    parent: Optional[Union["Background", "Scenario"]] = None
    failed: bool = False
    duration: Optional[float] = None

    @property
    def scenario(self) -> Optional["Scenario"]:
        """Returns the scenario if the step's parent is a Scenario."""
        if isinstance(self.parent, Scenario):
            return self.parent
        return None

    @property
    def background(self) -> Optional["Background"]:
        """Returns the background if the step's parent is a Background."""
        if isinstance(self.parent, Background):
            return self.parent
        return None

    def generate_initial_name(self) -> None:
        """Generate an initial name based on the step's text and optional docString."""
        self.name = strip_comments(self.text)
        if self.docString:
            self.name = f"{self.name}\n{self.docString.content}"
        # Populate a frozen copy of the name untouched by params later
        self.raw_name = self.name

    @model_validator(mode="after")
    def set_name(cls, instance):
        """Set the 'name' attribute after model validation if it is not already provided."""
        instance.generate_initial_name()
        return instance

    @field_validator("keyword", mode="before")
    def normalize_keyword(cls, value: str) -> str:
        """Normalize the keyword (e.g., Given, When, Then)."""
        return value.title().strip()

    @property
    def given_when_then(self) -> str:
        """Get the Given/When/Then form of the step."""
        return self._gwt

    @given_when_then.setter
    def given_when_then(self, gwt: str) -> None:
        """Set the Given/When/Then form of the step."""
        self._gwt = gwt

    def __str__(self) -> str:
        """Return a string representation of the step."""
        return f'{self.given_when_then.capitalize()} "{self.name}"'

    @property
    def params(self) -> Tuple[str, ...]:
        """Get the parameters in the step name."""
        return tuple(frozenset(STEP_PARAM_RE.findall(self.raw_name)))

    def render(self, context: Mapping[str, Any]) -> None:
        """Render the step name with the given context and update the instance.

        Args:
            context (Mapping[str, Any]): The context for rendering the step name.
        """

        def replacer(m: re.Match) -> str:
            varname = m.group(1)
            # If the context contains the variable, replace it. Otherwise, leave it unchanged.
            return str(context.get(varname, f"<{varname}>"))

        # Render the name and update the instance's text attribute
        rendered_name = STEP_PARAM_RE.sub(replacer, self.raw_name)
        self.name = rendered_name


class Tag(BaseModel):
    id: str
    location: Location
    name: str


class Scenario(BaseModel):
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    steps: List[Step]
    tags: List[Tag]
    examples: Optional[List[DataTable]] = None
    parent: Optional[Union["Feature", "Rule"]] = None

    @field_validator("description", mode="before")
    def dedent_description(cls, value: str) -> str:
        return textwrap.dedent(value)

    @model_validator(mode="after")
    def process_steps(cls, instance):
        steps = instance.steps
        instance.steps = _compute_given_when_then(steps)
        return instance

    @model_validator(mode="after")
    def process_scenario_for_steps(cls, instance):
        for step in instance.steps:
            step.parent = instance
        return instance

    @property
    def tag_names(self) -> List[str]:
        return get_tag_names(self.tags)

    def render(self, context: Mapping[str, Any]) -> None:
        """Render the scenario's steps with the given context.

        Args:
            context (Mapping[str, Any]): The context for rendering steps.
        """
        for step in self.steps:
            step.render(context)

    @property
    def feature(self):
        if check_instance_by_name(self.parent, "Feature"):
            return self.parent
        return None

    @property
    def rule(self):
        if check_instance_by_name(self.parent, "Rule"):
            return self.parent
        return None

    @property
    def all_steps(self) -> List[Step]:
        """Get all steps including background steps if present."""
        # Check if the scenario belongs to a feature and if the feature has background steps
        background_steps = self.feature.background_steps if self.feature else []
        # Return the combined list of background steps and scenario steps
        return background_steps + self.steps


class Rule(BaseModel):
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    tags: List[Tag]
    children: List[Scenario]
    parent: Optional["Feature"] = None

    @field_validator("description", mode="before")
    def dedent_description(cls, value: str) -> str:
        return textwrap.dedent(value)

    @model_validator(mode="after")
    def process_scenarios(cls, instance):
        for scenario in instance.children:
            scenario.parent = instance
        return instance

    @property
    def tag_names(self) -> List[str]:
        return get_tag_names(self.tags)


class Background(BaseModel):
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    steps: List[Step]
    parent: Optional["Feature"] = None

    @field_validator("description", mode="before")
    def dedent_description(cls, value: str) -> str:
        return textwrap.dedent(value)

    @model_validator(mode="after")
    def process_given_when_then(cls, instance):
        steps = instance.steps
        instance.steps = _compute_given_when_then(steps)
        return instance

    @model_validator(mode="after")
    def process_background_for_steps(cls, instance):
        for step in instance.steps:
            step.parent = instance
        return instance

    def render(self, context: Mapping[str, Any]) -> None:
        """Render the scenario's steps with the given context.

        Args:
            context (Mapping[str, Any]): The context for rendering steps.
        """
        for step in self.steps:
            step.render(context)


class Child(BaseModel):
    background: Optional[Background] = None
    rule: Optional[Rule] = None
    scenario: Optional[Scenario] = None
    parent: Optional[Union["Feature", "Rule"]] = None

    @model_validator(mode="after")
    def assign_parents(cls, instance):
        if instance.scenario:
            instance.scenario.parent = instance.parent
        if instance.background:
            instance.background.parent = instance.parent
        return instance


class Feature(BaseModel):
    keyword: str
    location: Location
    tags: List[Tag]
    name: str
    description: str
    children: List[Child]
    abs_filename: Optional[str] = None
    rel_filename: Optional[str] = None

    @field_validator("description", mode="before")
    def dedent_description(cls, value: str) -> str:
        return textwrap.dedent(value)

    @model_validator(mode="after")
    def assign_child_parents(cls, instance):
        for child in instance.children:
            child.parent = instance
            if child.scenario:
                child.scenario.parent = instance
            if child.background:
                child.background.parent = instance
        return instance

    @property
    def filename(self) -> Optional[str]:
        """
        Returns the file name from abs_filename, if available.
        """
        if self.abs_filename:
            return str(Path(self.abs_filename).resolve())
        return None

    @property
    def scenarios(self) -> List[Scenario]:
        return [child.scenario for child in self.children if child.scenario]

    @property
    def backgrounds(self) -> List[Background]:
        return [child.background for child in self.children if child.background]

    @property
    def background_steps(self) -> List[Step]:
        _steps = []
        for background in self.backgrounds:
            _steps.extend(background.steps)
        return _steps

    @property
    def rules(self) -> List[Rule]:
        return [child.rule for child in self.children if child.rule]

    def get_child_by_name(self, name: str) -> Optional[Union[Scenario, Background]]:
        """
        Returns the child (Scenario or Background) that has the given name.
        """
        for scenario in self.scenarios:
            if scenario.name == name:
                return scenario
        for background in self.backgrounds:
            if background.name == name:
                return background
        return None

    @property
    def tag_names(self) -> List[str]:
        return get_tag_names(self.tags)


class GherkinDocument(BaseModel):
    feature: Feature
    comments: List[Comment]


def _compute_given_when_then(steps: List[Step]) -> List[Step]:
    last_gwt = None
    for step in steps:
        if step.keyword.lower() in STEP_TYPES:
            last_gwt = step.keyword.lower()
        step.given_when_then = last_gwt
    return steps


def get_tag_names(tags: List[Tag]):
    return [tag.name.lstrip("@") for tag in tags]


class GherkinParser:
    def __init__(self, abs_filename: str, rel_filename: str, encoding: str = "utf-8"):
        self.abs_filename = abs_filename
        self.rel_filename = rel_filename
        self.encoding = encoding

        with open(self.abs_filename, encoding=self.encoding) as f:
            self.feature_file_text = f.read()
        try:
            self.gherkin_data = Parser().parse(TokenScanner(self.feature_file_text))
        except CompositeParserException as e:
            raise exceptions.FeatureError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(self.abs_filename, e.errors[0].location["line"]).rstrip("\n"),
                self.abs_filename,
            ) from e

    def to_gherkin_document(self) -> GherkinDocument:
        gherkin_document = GherkinDocument(**self.gherkin_data)
        # Pass abs_filename to the feature
        gherkin_document.feature.abs_filename = self.abs_filename
        gherkin_document.feature.rel_filename = self.rel_filename
        return gherkin_document
