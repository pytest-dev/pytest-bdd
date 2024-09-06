import linecache
import textwrap
from pathlib import Path
from typing import List, Optional

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner
from pydantic import BaseModel, field_validator, model_validator

from . import exceptions
from .types import STEP_TYPES


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

    @field_validator("keyword", mode="before")
    def normalize_keyword(cls, value: str) -> str:
        return value.lower().strip()

    @property
    def given_when_then(self) -> str:
        return self._gwt

    @given_when_then.setter
    def given_when_then(self, gwt: str) -> None:
        self._gwt = gwt


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

    @model_validator(mode="after")
    def process_steps(cls, instance):
        steps = instance.steps
        instance.steps = _compute_given_when_then(steps)
        return instance


class Rule(BaseModel):
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    tags: List[Tag]
    children: List[Scenario]


class Background(BaseModel):
    id: str
    keyword: str
    location: Location
    name: str
    description: str
    steps: List[Step]

    @model_validator(mode="after")
    def process_steps(cls, instance):
        steps = instance.steps
        instance.steps = _compute_given_when_then(steps)
        return instance


class Child(BaseModel):
    background: Optional[Background] = None
    rule: Optional[Rule] = None
    scenario: Optional[Scenario] = None


class Feature(BaseModel):
    keyword: str
    location: Location
    tags: List[Tag]
    name: str
    description: str
    children: List[Child]


class GherkinDocument(BaseModel):
    feature: Feature
    comments: List[Comment]


def _compute_given_when_then(steps: list[Step]) -> list[Step]:
    last_gwt = None
    for step in steps:
        if step.keyword in STEP_TYPES:
            last_gwt = step.keyword
        step.given_when_then = last_gwt
    return steps


class GherkinParser:
    def __init__(self, abs_filename: str = None, encoding: str = "utf-8"):
        self.abs_filename = Path(abs_filename) if abs_filename else None
        self.encoding = encoding

        with open(self.abs_filename, encoding=self.encoding) as f:
            self.feature_file_text = f.read()
        try:
            self.gherkin_data = Parser().parse(TokenScanner(self.feature_file_text))
        except CompositeParserException as e:
            raise exceptions.FeatureError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(self.abs_filename), e.errors[0].location["line"]).rstrip("\n"),
                self.abs_filename,
            ) from e

    def to_gherkin_document(self) -> GherkinDocument:
        return GherkinDocument(**self.gherkin_data)
