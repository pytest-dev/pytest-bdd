import linecache
import textwrap
from typing import Any, Dict, List, Optional

import attr
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner

from . import exceptions
from .types import STEP_TYPES


@attr.s
class Location:
    column = attr.ib(type=int)
    line = attr.ib(type=int)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Location":
        return cls(column=data["column"], line=data["line"])


@attr.s
class Comment:
    location = attr.ib(type=Location)
    text = attr.ib(type=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Comment":
        return cls(location=Location.from_dict(data["location"]), text=data["text"])


@attr.s
class Cell:
    location = attr.ib(type=Location)
    value = attr.ib(type=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cell":
        return cls(location=Location.from_dict(data["location"]), value=_convert_to_raw_string(data["value"]))


@attr.s
class Row:
    id = attr.ib(type=str)
    location = attr.ib(type=Location)
    cells = attr.ib(type=List[Cell])

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Row":
        return cls(
            id=data["id"],
            location=Location.from_dict(data["location"]),
            cells=[Cell.from_dict(cell) for cell in data["cells"]],
        )


@attr.s
class DataTable:
    location = attr.ib(type=Location)
    name = attr.ib(type=Optional[str], default=None)
    tableHeader = attr.ib(type=Optional[Row], default=None)
    tableBody = attr.ib(type=Optional[List[Row]], factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataTable":
        return cls(
            location=Location.from_dict(data["location"]),
            name=data.get("name"),
            tableHeader=Row.from_dict(data["tableHeader"]) if data.get("tableHeader") else None,
            tableBody=[Row.from_dict(row) for row in data.get("tableBody", [])],
        )


@attr.s
class DocString:
    content = attr.ib(type=str)
    delimiter = attr.ib(type=str)
    location = attr.ib(type=Location)

    def __attrs_post_init__(self):
        self.content = textwrap.dedent(self.content)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DocString":
        return cls(content=data["content"], delimiter=data["delimiter"], location=Location.from_dict(data["location"]))


@attr.s
class Step:
    id = attr.ib(type=str)
    keyword = attr.ib(type=str)
    keywordType = attr.ib(type=str)
    location = attr.ib(type=Location)
    text = attr.ib(type=str)
    dataTable = attr.ib(type=Optional[DataTable], default=None)
    docString = attr.ib(type=Optional[DocString], default=None)

    def __attrs_post_init__(self):
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


@attr.s
class Tag:
    id = attr.ib(type=str)
    location = attr.ib(type=Location)
    name = attr.ib(type=str)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Tag":
        return cls(id=data["id"], location=Location.from_dict(data["location"]), name=data["name"])


@attr.s
class Scenario:
    id = attr.ib(type=str)
    keyword = attr.ib(type=str)
    location = attr.ib(type=Location)
    name = attr.ib(type=str)
    description = attr.ib(type=str)
    steps = attr.ib(type=List[Step])
    tags = attr.ib(type=List[Tag])
    examples = attr.ib(type=Optional[List[DataTable]], factory=list)

    def __attrs_post_init__(self):
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


@attr.s
class Rule:
    id = attr.ib(type=str)
    keyword = attr.ib(type=str)
    location = attr.ib(type=Location)
    name = attr.ib(type=str)
    description = attr.ib(type=str)
    tags = attr.ib(type=List[Tag])
    children = attr.ib(type=List[Scenario])

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


@attr.s
class Background:
    id = attr.ib(type=str)
    keyword = attr.ib(type=str)
    location = attr.ib(type=Location)
    name = attr.ib(type=str)
    description = attr.ib(type=str)
    steps = attr.ib(type=List[Step])

    def __attrs_post_init__(self):
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


@attr.s
class Child:
    background = attr.ib(type=Optional[Background], default=None)
    rule = attr.ib(type=Optional[Rule], default=None)
    scenario = attr.ib(type=Optional[Scenario], default=None)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Child":
        return cls(
            background=Background.from_dict(data["background"]) if data.get("background") else None,
            rule=Rule.from_dict(data["rule"]) if data.get("rule") else None,
            scenario=Scenario.from_dict(data["scenario"]) if data.get("scenario") else None,
        )


@attr.s
class Feature:
    keyword = attr.ib(type=str)
    location = attr.ib(type=Location)
    tags = attr.ib(type=List[Tag])
    name = attr.ib(type=str)
    description = attr.ib(type=str)
    children = attr.ib(type=List[Child])

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


@attr.s
class GherkinDocument:
    feature = attr.ib(type=Feature)
    comments = attr.ib(type=List[Comment])

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

    # Assuming gherkin_data is a dictionary with the structure expected by from_dict methods
    return GherkinDocument.from_dict(gherkin_data)
