from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, cast

from attr import Factory, attrib, attrs
from marshmallow import Schema, fields, post_load

from pytest_bdd.ast import Scenario as ASTScenario
from pytest_bdd.ast import Step as ASTStep
from pytest_bdd.ast import TableRow as ASTTableRow
from pytest_bdd.const import STEP_PREFIXES, TAG
from pytest_bdd.utils import ModelSchemaPostLoadable, _itemgetter, deepattrgetter

if TYPE_CHECKING:  # pragma: no cover
    from pytest_bdd.model.feature import Feature


@attrs
class ASTLinkMixin:
    ast = attrib(init=False)

    @property
    def linked_ast_nodes(self):
        return _itemgetter(
            *((self.ast_node_id,) if hasattr(self, "ast_node_id") else ()),
            *getattr(self, "ast_node_ids", ()),
        )(self.ast.registry)


@attrs
class ASTNodeIDsMixin(ASTLinkMixin):
    ast_node_ids: list[str] = attrib()


class ASTNodeIDsSchemaMixin(Schema):
    ast_node_ids = fields.List(fields.Str(), data_key="astNodeIds")


@attrs
class Cell(ModelSchemaPostLoadable):
    value: str = attrib()


class CellSchema(Schema):
    value = fields.Str()

    build_cell = Cell.schema_post_loader()


@attrs
class Row(ModelSchemaPostLoadable):
    cells: list[Cell] = attrib()


class RowSchema(Schema):
    cells = fields.Nested(CellSchema(many=True))

    build_row = Row.schema_post_loader()


@attrs
class DataTable(ModelSchemaPostLoadable):
    rows: list[Row] = attrib()


class DataTableSchema(Schema):
    rows = fields.Nested(RowSchema(many=True))

    build_data_table = DataTable.schema_post_loader()


@attrs
class DocString(ModelSchemaPostLoadable):
    content: str = attrib()
    # Workaround because of allure integration
    if TYPE_CHECKING:  # pragma: no cover
        media_type: str = attrib(init=False)

    postbuild_attrs = ["media_type"]


class DocStringSchema(Schema):
    content = fields.Str()
    media_type = fields.Str(data_key="mediaType", required=False)

    build_doc_string = DocString.schema_post_loader()


@attrs
class Argument(ModelSchemaPostLoadable):
    # Workaround because of allure integration
    if TYPE_CHECKING:  # pragma: no cover
        data_table: DataTable = attrib(init=False)
        doc_string: DocString = attrib(init=False)

    postbuild_attrs = ["data_table", "doc_string"]


class ArgumentSchema(Schema):
    data_table = fields.Nested(DataTableSchema(), data_key="dataTable", required=False)
    doc_string = fields.Nested(DocStringSchema(), data_key="docString", required=False)

    build_argument = Argument.schema_post_loader()


@attrs
class Step(ASTNodeIDsMixin, ModelSchemaPostLoadable):
    id: str = attrib()
    text: str = attrib()
    # Workaround because of allure integration
    if TYPE_CHECKING:  # pragma: no cover
        argument: Argument = attrib(init=False)

    postbuild_attrs = ["argument"]

    # region Indirectly loadable
    scenario = attrib(init=False)
    # endregion

    @property
    def _ast_step(self) -> ASTStep:
        return cast(ASTStep, next(filter(lambda node: type(node) is ASTStep, self.linked_ast_nodes)))

    @property
    def prefix(self):
        return self.keyword.lower()

    @property
    def name(self):
        return self.text

    @property
    def keyword(self):
        return self._ast_step.keyword.strip()

    @property
    def line_number(self):
        return self._ast_step.location.line

    @property
    def doc_string(self):
        return self._ast_step.doc_string

    @property
    def data_table(self):
        return self._ast_step.data_table

    def decompose(self):
        self.ast = None
        self.scenario = None


class StepSchema(ASTNodeIDsSchemaMixin, Schema):
    argument = fields.Nested(ArgumentSchema(), required=False)
    id = fields.Str()
    text = fields.Str()

    build_step = Step.schema_post_loader()


@attrs
class Tag(ASTLinkMixin, ModelSchemaPostLoadable):
    ast_node_id: str = attrib()
    name: str = attrib()

    def decompose(self):
        self.ast = None


class TagSchema(Schema):
    ast_node_id = fields.Str(data_key="astNodeId")
    name = fields.Str()

    build_tag = Tag.schema_post_loader()


@attrs
class Scenario(ASTNodeIDsMixin, ModelSchemaPostLoadable):
    id: str = attrib()
    name: str = attrib()
    language: str = attrib()
    steps: list[Step] = attrib()
    tags: list[Tag] = attrib()
    uri: str = attrib()

    # region Indirectly loadable
    feature: Feature = attrib(init=False)
    # endregion

    @property
    def _ast_scenario(self) -> ASTScenario:
        return cast(ASTScenario, next(filter(lambda node: type(node) is ASTScenario, self.linked_ast_nodes)))

    @property
    def _ast_table_rows(self) -> list[ASTTableRow]:
        return list(filter(lambda node: type(node) is ASTTableRow, self.linked_ast_nodes))

    @property
    def table_rows_breadcrumb(self):
        table_rows_lines = ",".join(
            map(lambda row: f"line: {deepattrgetter('location.line', default=-1)(row)[0]}", self._ast_table_rows)
        )
        return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""

    @property
    def line_number(self):
        return self._ast_scenario.location.line

    @property
    def tag_names(self):
        return sorted(map(lambda tag: tag.name.lstrip(STEP_PREFIXES[TAG]), self.tags))

    def bind_ast(self, ast):
        self.ast = ast

        for step in self.steps:
            step.ast = ast

        for tag in self.tags:
            tag.ast = ast

    def bind_feature(self, feature: Feature):
        self.feature = feature

        self.bind_ast(feature.gherkin_ast)

    def bind_steps(self):
        for step in self.steps:
            step.scenario = self

    def decompose(self):
        self.feature = None
        self.ast = None
        for step in self.steps:
            step.decompose()
        for tag in self.tags:
            tag.decompose()


class ScenarioSchema(ASTNodeIDsSchemaMixin, Schema):
    id = fields.Str()
    name = fields.Str()
    language = fields.Str()
    steps = fields.Nested(StepSchema(many=True))
    tags = fields.Nested(TagSchema(many=True))
    uri = fields.Str()

    @post_load
    def build_scenario(self, data, many, **kwargs):
        scenario = Scenario(**data)
        scenario.bind_steps()
        return scenario


@attrs
class UserStep:
    text: str = attrib()
    scenario = attrib()

    id: str = attrib(default=Factory(lambda: str(uuid.uuid4())))
    argument: Argument = attrib(default=None)
    keyword = attrib(default="Given")
    line_number = attrib(default=-1)
    doc_string: DocString | None = attrib(default=None)
    data_table: DataTable | None = attrib(default=None)

    @property
    def prefix(self):
        return self.keyword.lower()

    @property
    def name(self):
        return self.text

    def decompose(self):
        self.scenario = None
