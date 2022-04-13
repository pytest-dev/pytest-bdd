from __future__ import annotations

from attr import attrib, attrs
from marshmallow import Schema, fields, post_load


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
class ASTNodeIDsMixin:
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


class StepSchema(Schema, ASTNodeIDsSchemaMixin):
    argument = fields.Nested(ArgumentSchema(), required=False)
    id = fields.Str()
    text = fields.Str()

    @post_load(pass_many=False)
    def build_step(self, data, many, **kwargs):
        return postbuild_attr_builder(Step, data, ["argument"])


@attrs
class Tag:
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


class PickleSchema(Schema, ASTNodeIDsSchemaMixin):
    id = fields.Str()
    name = fields.Str()
    language = fields.Str()
    steps = fields.Nested(StepSchema(many=True))
    tags = fields.Nested(TagSchema(many=True))
    uri = fields.Str()

    @post_load
    def build_pickle(self, data, many, **kwargs):
        return Pickle(**data)
