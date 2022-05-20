from __future__ import annotations

from typing import TYPE_CHECKING

from attr import attrib, attrs
from marshmallow import Schema, fields

from pytest_bdd.utils import ModelSchemaPostLoadable


@attrs
class AST(ModelSchemaPostLoadable):
    gherkin_document: GherkinDocument = attrib()

    @property
    def registry(self):
        return {**(self.gherkin_document.feature.registry if hasattr(self.gherkin_document, "feature") else {})}


class ASTSchema(Schema):
    gherkin_document = fields.Nested(lambda: GherkinDocumentSchema(), data_key="gherkinDocument")

    build_ast = AST.schema_post_loader()


@attrs
class GherkinDocument(ModelSchemaPostLoadable):
    comments: list[Comment] = attrib()
    uri: str = attrib()

    # Workaround because of allure integration
    if TYPE_CHECKING:  # pragma: no cover
        feature: Feature = attrib(init=False)

    postbuild_attrs = ["feature"]


class GherkinDocumentSchema(Schema):
    comments = fields.Nested(lambda: CommentSchema(many=True))
    feature = fields.Nested(lambda: FeatureSchema(), required=False)
    uri = fields.Str()

    build_gherkin_document = GherkinDocument.schema_post_loader()


@attrs
class Identifiable:
    identifier: str = attrib()

    @property
    def registry(self):
        return {self.identifier: self}


class IdentifiableSchema(Schema):
    identifier = fields.Str(data_key="id")


@attrs
class Tagable:
    tags: list[Tag] = attrib()

    @property
    def registry(self):
        registry = {}
        for tag in self.tags:
            registry.update(tag.registry)
        return registry


class TagableSchema(Schema):
    tags = fields.Nested(lambda: TagSchema(many=True))


@attrs
class Locatable:
    location: Location = attrib()


class LocatableSchema(Schema):
    location = fields.Nested(lambda: LocationSchema())


@attrs
class Keywordable:
    keyword: str = attrib()


class KeywordableSchema(Schema):
    keyword = fields.Str()


@attrs
class Descriptable:
    description: str = attrib()


class DescriptableSchema(Schema):
    description = fields.Str()


@attrs
class Nameable:
    name: str = attrib()


class NameableSchema(Schema):
    name = fields.Str()


@attrs
class Tag(Identifiable, Locatable, Nameable, ModelSchemaPostLoadable):
    ...


class TagSchema(IdentifiableSchema, LocatableSchema, NameableSchema):
    build_tag = Tag.schema_post_loader()


@attrs
class Comment(Locatable, ModelSchemaPostLoadable):
    text: str = attrib()


class CommentSchema(LocatableSchema, Schema):
    text = fields.Str()

    build_comment = Comment.schema_post_loader()


@attrs
class NodeProto(Locatable, Keywordable, Descriptable, Nameable):
    ...


class NodeProtoSchema(LocatableSchema, KeywordableSchema, DescriptableSchema, NameableSchema, Schema):
    ...


@attrs
class NodeContainerProto(NodeProto, Tagable):
    children: list[NodeContainerChild] = attrib()

    @property
    def registry(self):
        registry = {**Tagable.registry.__get__(self)}
        for child in self.children:
            registry.update(child.registry)
        return registry


class NodeContainerProtoSchema(NodeProtoSchema, TagableSchema, Schema):
    children = fields.Nested(lambda: NodeContainerChildSchema(many=True))


@attrs
class NodeStepContainerProto(NodeProto):
    steps: list[Step] = attrib()

    @property
    def registry(self):
        registry = {}
        for step in self.steps:
            registry.update(step.registry)
        return registry


class NodeStepContainerProtoSchema(NodeProtoSchema, Schema):
    steps = fields.Nested(lambda: StepSchema(many=True))


@attrs
class Feature(NodeContainerProto, ModelSchemaPostLoadable):
    language: str = attrib()
    keyword: str = attrib(init=False)

    postbuild_attrs = ["keyword"]


class FeatureSchema(NodeContainerProtoSchema, Schema):
    language = fields.Str()
    keyword = fields.Str(required=False)

    build_feature = Feature.schema_post_loader()


@attrs
class Rule(NodeContainerProto, Identifiable, ModelSchemaPostLoadable):
    @property
    def registry(self):
        return {
            **NodeContainerProto.registry.__get__(self),
            **Identifiable.registry.__get__(self),
        }


class RuleSchema(NodeContainerProtoSchema, IdentifiableSchema, Schema):
    build_rule = Rule.schema_post_loader()


@attrs
class Background(NodeStepContainerProto, Identifiable, ModelSchemaPostLoadable):
    @property
    def registry(self):
        return {
            **NodeStepContainerProto.registry.__get__(self),
            **Identifiable.registry.__get__(self),
        }


class BackgroundSchema(NodeStepContainerProtoSchema, IdentifiableSchema, Schema):
    build_background = Background.schema_post_loader()


@attrs
class Scenario(NodeStepContainerProto, Identifiable, Tagable, ModelSchemaPostLoadable):
    examples: list[Example] = attrib()

    @property
    def registry(self):
        registry = {
            **NodeStepContainerProto.registry.__get__(self),
            **Identifiable.registry.__get__(self),
            **Tagable.registry.__get__(self),
        }
        for example in self.examples:
            registry.update(example.registry)
        return registry


class ScenarioSchema(NodeStepContainerProtoSchema, IdentifiableSchema, TagableSchema, Schema):
    examples = fields.Nested(lambda: ExampleSchema(many=True))

    build_scenario = Scenario.schema_post_loader()


@attrs
class NodeContainerChild(ModelSchemaPostLoadable):

    # Workaround because of allure integration
    if TYPE_CHECKING:  # pragma: no cover
        background: Background = attrib(init=False)
        scenario: Scenario = attrib(init=False)
        rule: Rule = attrib(init=False)

    postbuild_attrs = ["background", "scenario", "rule"]

    @property
    def registry(self):
        registry = {
            **(self.background.registry if hasattr(self, "background") else {}),
            **(self.scenario.registry if hasattr(self, "scenario") else {}),
            **(self.rule.registry if hasattr(self, "rule") else {}),
        }
        return registry


class NodeContainerChildSchema(Schema):
    background = fields.Nested(lambda: BackgroundSchema(), required=False)
    scenario = fields.Nested(lambda: ScenarioSchema(), required=False)
    rule = fields.Nested(lambda: RuleSchema(), required=False)

    build_node_container_child = NodeContainerChild.schema_post_loader()


@attrs
class Location(ModelSchemaPostLoadable):
    column: int = attrib()
    line: int = attrib()


class LocationSchema(Schema):
    column = fields.Int()
    line = fields.Int()

    build_loc = Location.schema_post_loader()


@attrs
class DocString(Locatable, ModelSchemaPostLoadable):
    content: str = attrib()
    delimiter: str = attrib()

    # Workaround because of allure integration
    if TYPE_CHECKING:  # pragma: no cover
        media_type: str = attrib(init=False)

    postbuild_attrs = ["media_type"]


class DocStringSchema(LocatableSchema, Schema):
    content = fields.Str()
    delimiter = fields.Str()
    media_type = fields.Str(required=False, data_key="mediaType")

    build_docstring = DocString.schema_post_loader()


@attrs
class Step(Identifiable, Keywordable, Locatable, ModelSchemaPostLoadable):
    text: str = attrib()

    # Workaround because of allure integration
    if TYPE_CHECKING:  # pragma: no cover
        data_table: DataTable = attrib(init=False)
        doc_string: DocString = attrib(init=False)

    postbuild_attrs = ["data_table", "doc_string"]

    @property
    def registry(self):
        registry = {
            **Identifiable.registry.__get__(self),
            **(self.data_table.registry if hasattr(self, "data_table") else {}),
        }
        return registry


class StepSchema(IdentifiableSchema, KeywordableSchema, LocatableSchema, Schema):
    text = fields.Str()
    data_table = fields.Nested(lambda: DataTableSchema(), data_key="dataTable", required=False)
    doc_string = fields.Nested(lambda: DocStringSchema(), data_key="docString", required=False)

    build_step = Step.schema_post_loader()


@attrs
class Example(Descriptable, Identifiable, Keywordable, Locatable, Nameable, Tagable, ModelSchemaPostLoadable):
    table_body: list[TableRow] = attrib()

    # Workaround because of allure integration
    if TYPE_CHECKING:  # pragma: no cover
        table_header: ExampleTableHeader = attrib(init=False)

    postbuild_attrs = ["table_header"]

    @property
    def registry(self):
        registry = {
            **Identifiable.registry.__get__(self),
            **(self.table_header.registry if hasattr(self, "table_header") else {}),
        }
        for table_row in self.table_body:
            registry.update(table_row.registry)
        return registry


class ExampleSchema(
    DescriptableSchema, IdentifiableSchema, KeywordableSchema, LocatableSchema, NameableSchema, TagableSchema, Schema
):
    table_body = fields.Nested(lambda: TableRowSchema(many=True), data_key="tableBody")
    table_header = fields.Nested(lambda: TableHeaderSchema(), data_key="tableHeader", required=False)

    build_example = Example.schema_post_loader()


@attrs
class TableRow(Identifiable, Locatable, ModelSchemaPostLoadable):
    cells: list[TableCell] = attrib()


class TableRowSchema(IdentifiableSchema, LocatableSchema, Schema):
    cells = fields.Nested(lambda: TableCellSchema(many=True))

    build_table_row = TableRow.schema_post_loader()


@attrs
class ExampleTableHeader(TableRow):
    ...


class TableHeaderSchema(TableRowSchema, Schema):
    ...


@attrs
class TableCell(Locatable, ModelSchemaPostLoadable):
    value: str = attrib()


class TableCellSchema(LocatableSchema, Schema):
    value = fields.Str()

    build_cell = TableCell.schema_post_loader()


@attrs
class DataTable(Locatable, ModelSchemaPostLoadable):
    rows: list[TableRow] = attrib()

    @property
    def registry(self):
        registry = {}
        for row in self.rows:
            registry.update(row.registry)
        return registry


class DataTableSchema(LocatableSchema, Schema):
    rows = fields.Nested(lambda: TableRowSchema(many=True))

    build_datatable = DataTable.schema_post_loader()
