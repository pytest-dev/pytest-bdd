from marshmallow import Schema, fields


class ASTNodeIDsMixin:
    ast_node_ids = fields.List(fields.Str(), data_key="astNodeIds")


class Pickle(Schema, ASTNodeIDsMixin):
    id = fields.Str()
    name = fields.Str()
    language = fields.Str()
    steps = fields.List(fields.Nested(lambda: Step))
    tags = fields.List(fields.Nested(lambda: Tag()))
    uri = fields.Str()


class Step(Schema, ASTNodeIDsMixin):
    argument = fields.Nested(lambda: Argument)
    id = fields.Str()
    text = fields.Str()


class DataTable(Schema):
    rows = fields.List(fields.Nested(lambda: Row()))


class Row(Schema):
    cells = fields.List(fields.Nested(lambda: Cell()))


class Cell(Schema):
    value = fields.Str()


class Tag(Schema):
    ast_node_id = fields.Str(data_key="astNodeId")
    name = fields.Str()


class Argument(Schema):
    data_table = fields.Nested(lambda: DataTable, data_key="dataTable")
    doc_string = fields.Nested(lambda: DocString, data_key="docString")


class DocString(Schema):
    content = fields.Str()
    media_type = fields.Str(data_key="mediaType")
