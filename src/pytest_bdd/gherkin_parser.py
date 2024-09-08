import linecache
import textwrap
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner

from . import exceptions
from .types import STEP_TYPES


@dataclass
class Location:
    column: int
    line: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        return cls(column=data["column"], line=data["line"])


@dataclass
class Comment:
    location: Location
    text: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Comment":
        return cls(location=Location.from_dict(data["location"]), text=data["text"])


@dataclass
class Cell:
    location: Location
    value: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cell":
        return cls(location=Location.from_dict(data["location"]), value=_convert_to_raw_string(data["value"]))


@dataclass
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


@dataclass
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


@dataclass
class DocString:
    content: str
    delimiter: str
    location: Location

    def __post_init__(self):
        self.content = textwrap.dedent(self.content)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocString":
        return cls(content=data["content"], delimiter=data["delimiter"], location=Location.from_dict(data["location"]))


@dataclass
class Step:
    id: str
    keyword: str
    keywordType: str
    location: Location
    text: str
    dataTable: Optional[DataTable] = None
    docString: Optional[DocString] = None

    def __post_init__(self):
        self.keyword = self.keyword.lower().strip()

    @property
    def given_when_then(self) -> str:
        return getattr(self, "_gwt", "")

    @given_when_then.setter
    def given_when_then(self, gwt: str) -> None:
        self._gwt = gwt

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            keywordType=data["keywordType"],
            location=Location.from_dict(data["location"]),
            text=data["text"],
            dataTable=DataTable.from_dict(data["dataTable"]) if data.get("dataTable") else None,
            docString=DocString.from_dict(data["docString"]) if data.get("docString") else None,
        )


@dataclass
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
    tags: List[Tag]
    examples: Optional[List[DataTable]] = field(default_factory=list)

    def __post_init__(self):
        self.steps = _compute_given_when_then(self.steps)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Scenario":
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            name=data["name"],
            description=data["description"],
            steps=[Step.from_dict(step) for step in data["steps"]],
            tags=[Tag.from_dict(tag) for tag in data["tags"]],
            examples=[DataTable.from_dict(example) for example in data.get("examples", [])],
        )


@dataclass
class Rule:
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    tags: List[Tag]
    children: List[Scenario]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rule":
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            name=data["name"],
            description=data["description"],
            tags=[Tag.from_dict(tag) for tag in data["tags"]],
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

    def __post_init__(self):
        self.steps = _compute_given_when_then(self.steps)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Background":
        return cls(
            id=data["id"],
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            name=data["name"],
            description=data["description"],
            steps=[Step.from_dict(step) for step in data["steps"]],
        )


@dataclass
class Child:
    background: Optional[Background] = None
    rule: Optional[Rule] = None
    scenario: Optional[Scenario] = None

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
    tags: List[Tag]
    name: str
    description: str
    children: List[Child]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feature":
        return cls(
            keyword=data["keyword"],
            location=Location.from_dict(data["location"]),
            tags=[Tag.from_dict(tag) for tag in data["tags"]],
            name=data["name"],
            description=data["description"],
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
        if step.keyword in STEP_TYPES:
            last_gwt = step.keyword
        step.given_when_then = last_gwt
    return steps


def _convert_to_raw_string(normal_string: str) -> str:
    return normal_string.replace("\\", "\\\\")


def get_gherkin_document(abs_filename: str = None, encoding: str = "utf-8") -> GherkinDocument:
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

    return GherkinDocument.from_dict(gherkin_data)
