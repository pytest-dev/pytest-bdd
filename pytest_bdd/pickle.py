from __future__ import annotations

from typing import TYPE_CHECKING, cast

from attr import attrib, attrs
from marshmallow import Schema, fields, post_load

from .ast import Scenario as ASTScenario
from .ast import Step as ASTStep
from .ast import TableRow as ASTTableRow
from .utils import _itemgetter

if TYPE_CHECKING:
    from .feature import Feature


# TODO: Unify with schema
def postbuild_attr_builder(cls, data, postbuild_args):
    _data = {**data}
    empty = object()
    postbuildable_args = []
    for argument in postbuild_args:
        value = _data.pop(argument, empty)
        if value is not empty:
            postbuildable_args.append((argument, value))
    instance = cls(**_data)
    for argument, value in postbuildable_args:
        setattr(instance, argument, value)
    return instance


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


class ASTNodeIDsSchemaMixin:
    ast_node_ids = fields.List(fields.Str(), data_key="astNodeIds")


@attrs
class Cell:
    value: str = attrib()


class CellSchema(Schema):
    value = fields.Str()

    @post_load
    def build_cell(self, data, many, **kwargs):
        return Cell(**data)


@attrs
class Row:
    cells: list[Cell] = attrib()


class RowSchema(Schema):
    cells = fields.Nested(CellSchema(many=True))

    @post_load
    def build_row(self, data, many, **kwargs):
        return Row(**data)


@attrs
class DataTable:
    rows: list[Row] = attrib()


class DataTableSchema(Schema):
    rows = fields.Nested(RowSchema(many=True))

    @post_load
    def build_data_tables(self, data, many, **kwargs):
        return DataTable(**data)


@attrs
class DocString:
    content: str = attrib()
    media_type: str = attrib(init=False)


class DocStringSchema(Schema):
    content = fields.Str()
    media_type = fields.Str(data_key="mediaType", required=False)

    @post_load
    def build_doc_string(self, data, many, **kwargs):
        return postbuild_attr_builder(DocString, data, ["media_type"])


@attrs
class Argument:
    data_table: DataTable = attrib(init=False)
    doc_string: DocString = attrib(init=False)


class ArgumentSchema(Schema):
    data_table = fields.Nested(DataTableSchema(), data_key="dataTable", required=False)
    doc_string = fields.Nested(DocStringSchema(), data_key="docString", required=False)

    @post_load
    def build_argument(self, data, many, **kwargs):
        return postbuild_attr_builder(Argument, data, ["data_table", "doc_string"])


@attrs
class Step(ASTNodeIDsMixin):
    id: str = attrib()
    text: str = attrib()
    argument: Argument = attrib(init=False)

    pickle = attrib(init=False)

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


class StepSchema(Schema, ASTNodeIDsSchemaMixin):
    argument = fields.Nested(ArgumentSchema(), required=False)
    id = fields.Str()
    text = fields.Str()

    @post_load(pass_many=False)
    def build_step(self, data, many, **kwargs):
        return postbuild_attr_builder(Step, data, ["argument"])


@attrs
class Tag(ASTLinkMixin):
    ast_node_id: str = attrib()
    name: str = attrib()


class TagSchema(Schema):
    ast_node_id = fields.Str(data_key="astNodeId")
    name = fields.Str()

    @post_load
    def build_tag(self, data, many, **kwargs):
        return Tag(**data)


@attrs
class Pickle(ASTNodeIDsMixin):
    id: str = attrib()
    name: str = attrib()
    language: str = attrib()
    steps: list[Step] = attrib()
    tags: list[Tag] = attrib()
    uri: str = attrib()

    feature: Feature = attrib(init=False)

    @property
    def _ast_scenario(self) -> ASTScenario:
        return cast(ASTScenario, next(filter(lambda node: type(node) is ASTScenario, self.linked_ast_nodes)))

    @property
    def _ast_table_rows(self) -> list[ASTTableRow]:
        return list(filter(lambda node: type(node) is ASTTableRow, self.linked_ast_nodes))

    @property
    def table_rows_breadcrumb(self):
        table_rows_lines = ",".join(map(lambda row: f"line: {row.location.line}", self._ast_table_rows))
        return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""

    @property
    def line_number(self):
        return self._ast_scenario.location.line

    @property
    def tag_names(self):
        # TODO check '@' usage
        return sorted(map(lambda tag: tag.name.lstrip("@"), self.tags))

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
            step.pickle = self


class PickleSchema(Schema, ASTNodeIDsSchemaMixin):
    id = fields.Str()
    name = fields.Str()
    language = fields.Str()
    steps = fields.Nested(StepSchema(many=True))
    tags = fields.Nested(TagSchema(many=True))
    uri = fields.Str()

    @post_load
    def build_pickle(self, data, many, **kwargs):
        pickle = Pickle(**data)
        pickle.bind_steps()
        return pickle
