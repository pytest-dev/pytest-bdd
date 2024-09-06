import linecache
from pathlib import Path
from typing import List, Optional, Union

from gherkin.errors import CompositeParserException
from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner
from pydantic import BaseModel


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


class Step(BaseModel):
    id: str
    keyword: str
    keywordType: str
    location: Location
    text: str
    dataTable: Optional[DataTable] = None
    docString: Optional[DocString] = None


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


class GherkinParser:
    def __init__(self, abs_filename: str = None, encoding: str = "utf-8"):
        self.abs_filename = Path(abs_filename) if abs_filename else None
        self.encoding = encoding

        with open(self.abs_filename, encoding=self.encoding) as f:
            self.feature_file_text = f.read()
        try:
            self.gherkin_data = Parser().parse(TokenScanner(self.feature_file_text))
        except CompositeParserException as e:
            from src.pytest_bdd import exceptions

            raise exceptions.FeatureError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(self.abs_filename), e.errors[0].location["line"]).rstrip("\n"),
                self.abs_filename,
            ) from e

    def to_gherkin_document(self) -> GherkinDocument:
        return GherkinDocument(**self.gherkin_data)
