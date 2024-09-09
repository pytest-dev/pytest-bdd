import linecache
import re
import textwrap
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Union

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner

from . import exceptions
from .types import STEP_TYPES

STEP_PARAM_RE = re.compile(r"<(.+?)>")
COMMENT_RE = re.compile(r"(^|(?<=\s))#")


@dataclass(frozen=True)
class Location:
    column: int
    line: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        return cls(column=data["column"], line=data["line"])


@dataclass(frozen=True)
class Comment:
    location: Location
    text: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Comment":
        return cls(location=Location.from_dict(data["location"]), text=data["text"])


@dataclass(frozen=True)
class Cell:
    location: Location
    value: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cell":
        return cls(location=Location.from_dict(data["location"]), value=_convert_to_raw_string(data["value"]))


@dataclass(frozen=True)
class Row:
    id: str
    location: Location
    cells: List[Cell]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Row":
        return cls(
            id=data["id"],
            location=Location.from_dict(data["location"]),
            cells=[Cell.from_dict(cell) for cell in data["cells"]],
        )


@dataclass(frozen=True)
class DataTable:
    location: Location
    name: Optional[str] = None
    tableHeader: Optional[Row] = None
    tableBody: Optional[List[Row]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataTable":
        return cls(
            location=Location.from_dict(data["location"]),
            name=data.get("name"),
            tableHeader=Row.from_dict(data["tableHeader"]) if data.get("tableHeader") else None,
            tableBody=[Row.from_dict(row) for row in data.get("tableBody", [])],
        )

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


@dataclass(frozen=True)
class DocString:
    content: str
    delimiter: str
    location: Location

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocString":
        return cls(
            content=textwrap.dedent(data["content"]),
            delimiter=data["delimiter"],
            location=Location.from_dict(data["location"]),
        )


@dataclass
class Step:
    id: str
    keyword: str
    keywordType: str
    location: Location
    text: str
    name: Optional[str] = None
    raw_name: Optional[str] = None
    dataTable: Optional[DataTable] = None
    docString: Optional[DocString] = None
    parent: Optional[Union["Background", "Scenario"]] = None
    failed: bool = False
    duration: Optional[float] = None

    def __post_init__(self):
        def generate_initial_name():
            """Generate an initial name based on the step's text and optional docString."""
            self.name = _strip_comments(self.text)
            if self.docString:
                self.name = f"{self.name}\n{self.docString.content}"
            # Populate a frozen copy of the name untouched by params later
            self.raw_name = self.name

        generate_initial_name()
        self.params = tuple(frozenset(STEP_PARAM_RE.findall(self.raw_name)))

    def get_parent_of_type(self, parent_type) -> Optional[Any]:
        """Return the parent if it's of the specified type."""
        return self.parent if isinstance(self.parent, parent_type) else None

    @property
    def scenario(self) -> Optional["Scenario"]:
        return self.get_parent_of_type(Scenario)

    @property
    def background(self) -> Optional["Background"]:
        return self.get_parent_of_type(Background)

    @property
    def given_when_then(self) -> str:
        return getattr(self, "_gwt", "")

    @given_when_then.setter
    def given_when_then(self, gwt: str) -> None:
        self._gwt = gwt

    def __str__(self) -> str:
        """Return a string representation of the step."""
        return f'{self.given_when_then.capitalize()} "{self.name}"'

    def render(self, context: Mapping[str, Any]) -> None:
        """Render the step name with the given context and update the instance.

        Args:
            context (Mapping[str, Any]): The context for rendering the step name.
        """
        _render_steps([self], context)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        return cls(
            id=data["id"],
            keyword=str(data["keyword"]).capitalize().strip(),
            keywordType=data["keywordType"],
            location=Location.from_dict(data["location"]),
            text=data["text"],
            dataTable=DataTable.from_dict(data["dataTable"]) if data.get("dataTable") else None,
            docString=DocString.from_dict(data["docString"]) if data.get("docString") else None,
        )


@dataclass(frozen=True)
class Tag:
    id: str
    location: Location
    name: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tag":
        return cls(id=data["id"], location=Location.from_dict(data["location"]), name=data["name"])


@dataclass
class Scenario:
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    steps: List[Step]
    tags: Set[Tag]
    examples: Optional[List[DataTable]] = field(default_factory=list)
    parent: Optional[Union["Feature", "Rule"]] = None

    def __post_init__(self):
        self.steps = _compute_given_when_then(self.steps)
        for step in self.steps:
            step.parent = self

    @cached_property
    def tag_names(self) -> Set[str]:
        return _get_tag_names(self.tags)

    def render(self, context: Mapping[str, Any]) -> None:
        """Render the scenario's steps with the given context.

        Args:
            context (Mapping[str, Any]): The context for rendering steps.
        """
        _render_steps(self.steps, context)

    @cached_property
    def feature(self):
        return self.parent if _check_instance_by_name(self.parent, "Feature") else None

    @cached_property
    def rule(self):
        return self.parent if _check_instance_by_name(self.parent, "Rule") else None

    @property
    def all_steps(self) -> List[Step]:
        """Get all steps including background steps if present."""
        background_steps = self.feature.background_steps if self.feature else []
        return background_steps + self.steps

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            name=data["name"],
            description=textwrap.dedent(data["description"]),
            steps=[Step.from_dict(step) for step in data["steps"]],
            tags={Tag.from_dict(tag) for tag in data["tags"]},
            examples=[DataTable.from_dict(example) for example in data.get("examples", [])],
        )


@dataclass
class Rule:
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    tags: Set[Tag]
    children: List[Scenario]
    parent: Optional["Feature"] = None

    def __post_init__(self):
        for scenario in self.children:
            scenario.parent = self

    @cached_property
    def tag_names(self) -> Set[str]:
        return _get_tag_names(self.tags)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            name=data["name"],
            description=textwrap.dedent(data["description"]),
            tags={Tag.from_dict(tag) for tag in data["tags"]},
            children=[Scenario.from_dict(child) for child in data["children"]],
        )


@dataclass
class Background:
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    steps: List[Step]
    parent: Optional["Feature"] = None

    def __post_init__(self):
        self.steps = _compute_given_when_then(self.steps)
        for step in self.steps:
            step.parent = self

    def render(self, context: Mapping[str, Any]) -> None:
        """Render the scenario's steps with the given context.

        Args:
            context (Mapping[str, Any]): The context for rendering steps.
        """
        _render_steps(self.steps, context)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Background":
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            name=data["name"],
            description=textwrap.dedent(data["description"]),
            steps=[Step.from_dict(step) for step in data["steps"]],
        )


@dataclass
class Child:
    background: Optional[Background] = None
    rule: Optional[Rule] = None
    scenario: Optional[Scenario] = None
    parent: Optional[Union["Feature", "Rule"]] = None

    def __post_init__(self):
        if self.scenario:
            self.scenario.parent = self.parent
        if self.background:
            self.background.parent = self.parent

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Child":
        return cls(
            background=Background.from_dict(data["background"]) if data.get("background") else None,
            rule=Rule.from_dict(data["rule"]) if data.get("rule") else None,
            scenario=Scenario.from_dict(data["scenario"]) if data.get("scenario") else None,
        )


@dataclass
class Feature:
    keyword: str
    location: Location
    tags: Set[Tag]
    name: str
    description: str
    children: List[Child]
    abs_filename: Optional[str] = None
    rel_filename: Optional[str] = None

    def __post_init__(self):
        for child in self.children:
            child.parent = self
            if child.scenario:
                child.scenario.parent = self
            if child.background:
                child.background.parent = self

    @property
    def scenarios(self) -> List[Scenario]:
        return [child.scenario for child in self.children if child.scenario]

    @property
    def backgrounds(self) -> List[Background]:
        return [child.background for child in self.children if child.background]

    @property
    def background_steps(self) -> List[Step]:
        _steps = []
        backgrounds = self.backgrounds
        for background in backgrounds:
            _steps.extend(background.steps)
        return _steps

    @cached_property
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

    @cached_property
    def tag_names(self) -> Set[str]:
        return _get_tag_names(self.tags)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feature":
        return cls(
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            tags={Tag.from_dict(tag) for tag in data["tags"]},
            name=data["name"],
            description=textwrap.dedent(data["description"]),
            children=[Child.from_dict(child) for child in data["children"]],
        )


@dataclass
class GherkinDocument:
    feature: Feature
    comments: List[Comment]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GherkinDocument":
        return cls(
            feature=Feature.from_dict(data["feature"]),
            comments=[Comment.from_dict(comment) for comment in data["comments"]],
        )


def _compute_given_when_then(steps: List[Step]) -> List[Step]:
    last_gwt = None
    for step in steps:
        lower_keyword = step.keyword.lower()
        if lower_keyword in STEP_TYPES:
            last_gwt = lower_keyword
        step.given_when_then = last_gwt
    return steps


def get_gherkin_document(abs_filename: str, rel_filename: str, encoding: str = "utf-8") -> GherkinDocument:
    with open(abs_filename, encoding=encoding) as f:
        feature_file_text = f.read()

    try:
        gherkin_data = Parser().parse(TokenScanner(feature_file_text))
    except CompositeParserException as e:
        raise exceptions.FeatureError(
            e.args[0],
            e.errors[0].location["line"],
            linecache.getline(abs_filename, e.errors[0].location["line"]).rstrip("\n"),
            abs_filename,
        ) from e

    gherkin_doc = GherkinDocument.from_dict(gherkin_data)
    gherkin_doc.feature.abs_filename = abs_filename
    gherkin_doc.feature.rel_filename = rel_filename
    return gherkin_doc


def _check_instance_by_name(obj: Any, class_name: str) -> bool:
    return obj.__class__.__name__ == class_name


def _strip_comments(line: str) -> str:
    """Remove comments from a line of text.

    Args:
        line (str): The line of text from which to remove comments.

    Returns:
        str: The line of text without comments, with leading and trailing whitespace removed.
    """
    if "#" not in line:
        return line
    if res := COMMENT_RE.search(line):
        line = line[: res.start()]
    return line.strip()


def _get_tag_names(tags: Set[Tag]):
    return {tag.name.lstrip("@") for tag in tags}


def _convert_to_raw_string(normal_string: str) -> str:
    return normal_string.replace("\\", "\\\\")


def _render_steps(steps: List[Step], context: Mapping[str, Any]) -> None:
    """
    Render multiple steps in batch by applying the context to each step's text.

    Args:
        steps (List[Step]): The list of steps to render.
        context (Mapping[str, Any]): The context to apply to the step names.
    """
    # Create a map of parameter replacements for all steps at once
    # This will store {param: replacement} for each variable found in steps
    replacements = {param: context.get(param, f"<{param}>") for step in steps for param in step.params}

    # Precompute replacement function
    def replacer(text: str) -> str:
        return STEP_PARAM_RE.sub(lambda m: replacements.get(m.group(1), m.group(0)), text)

    # Apply the replacement in batch
    for step in steps:
        step.name = replacer(step.raw_name)
