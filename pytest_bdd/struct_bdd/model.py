from __future__ import annotations

from collections import namedtuple
from functools import partial
from itertools import chain, product, starmap, zip_longest
from operator import attrgetter, eq, is_not
from pathlib import Path
from typing import cast

from attr import Factory, attrib, attrs
from gherkin.pickles.compiler import Compiler
from marshmallow import Schema, fields, post_load, pre_load
from marshmallow_polyfield import PolyField

from pytest_bdd.ast import GherkinDocumentSchema
from pytest_bdd.const import TYPE_KEYWORD_TYPE
from pytest_bdd.model import Feature
from pytest_bdd.utils import ModelSchemaPostLoadable, deepattrgetter


class CastableToStrField(fields.Str):
    def __init__(
        self,
        *args,
        strict=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.strict = strict

    def _deserialize(self, value, attr, data, **kwargs):
        if not self.strict and not isinstance(value, (str, bytes)):
            value = str(value)
        return super()._deserialize(value, attr, data, **kwargs)


@attrs
class Node:
    tags: list[str] = attrib(default=Factory(list))
    name: str | None = attrib(default=None)
    description: str | None = attrib(default=None)
    comments: list[str] = attrib(default=Factory(list))


class NodeSchema(Schema):
    tags = fields.List(fields.Str(), required=False, data_key="Tags")
    name = fields.Str(required=False, data_key="Name")
    description = fields.Str(required=False, data_key="Description")
    comments = fields.List(fields.Str(), required=False, data_key="Comments")


@attrs
class Step(Node, ModelSchemaPostLoadable):
    steps: list[Step] = attrib(default=Factory(list))
    action: str | None = attrib(default=None)
    type: str | None = attrib(default="*")

    data: list[Table | Join] = attrib(default=Factory(list))
    examples: list[Table | Join] = attrib(default=Factory(list))

    Route = namedtuple("Route", ["tags", "steps", "example_table"])

    @property
    def routes(self):
        for routes in (
            product(*map(attrgetter("routes"), self.steps))
            if self.steps
            else [[self.Route([], [], Table(parameters=[], values=[]))]]
        ):
            steps = [self, *chain.from_iterable(map(attrgetter("steps"), routes))]

            if self.examples:
                for _example_table in self.examples:
                    example_table = Join(tables=[*map(attrgetter("example_table"), routes), _example_table])
                    tags = list(
                        {*chain.from_iterable(map(attrgetter("tags"), routes)), *example_table.tags, *self.tags}
                    )

                    yield self.Route(
                        tags,
                        steps,
                        example_table,
                    )
            else:
                example_table = Join(tables=[*map(attrgetter("example_table"), routes)])
                tags = list({*chain.from_iterable(map(attrgetter("tags"), routes)), *example_table.tags, *self.tags})

                yield self.Route(
                    tags,
                    steps,
                    example_table,
                )

    @property
    def keyword_type(self):
        return TYPE_KEYWORD_TYPE[self.type]

    def build_feature(self, filename, uri, id_generator):
        from pytest_bdd.struct_bdd.ast_builder import GherkinDocumentBuilder

        gherkin_ast = GherkinDocumentBuilder(self).build(id_generator=id_generator)
        gherkin_ast.uri = uri
        gherkin_ast_data = GherkinDocumentSchema().dump(gherkin_ast)
        gherkin_document_ast = Feature.load_gherkin_document(gherkin_ast_data)

        scenarios_data = Compiler().compile(gherkin_ast_data)
        pickles = Feature.load_pickles(scenarios_data)

        feature = Feature(  # type: ignore[call-arg]
            gherkin_document=gherkin_document_ast,
            uri=uri,
            pickles=pickles,
            filename=filename,
        )

        feature.fill_registry()

        return feature

    @attrs
    class Locator:
        step: Step = attrib()
        filename = attrib()
        uri = attrib()

        def resolve(self, config):
            feature = self.step.build_feature(
                filename=self.filename, uri=self.uri, id_generator=config.pytest_bdd_id_generator
            )
            return zip_longest((), feature.pickles, fillvalue=feature)

    def as_test(self, filename):
        from pytest_bdd.scenario import scenarios

        return scenarios(
            locators=[self.Locator(self, str(Path(filename).as_posix()), str(Path(filename).relative_to(Path.cwd())))],
            return_test_decorator=False,
        )

    def as_test_decorator(self, filename):
        from pytest_bdd.scenario import scenarios

        return scenarios(
            locators=[self.Locator(self, str(Path(filename).as_posix()), str(Path(filename).relative_to(Path.cwd())))],
            return_test_decorator=True,
        )

    @staticmethod
    def from_dict(_dict) -> Step:
        return cast(Step, StepSchema().load(_dict))


class Given(Step):
    def __new__(cls, action, *args, **kwargs):
        return Step(*args, type="Given", action=action, **kwargs)


class When(Step):
    def __new__(cls, action, *args, **kwargs):
        return Step(*args, type="When", action=action, **kwargs)


class Then(Step):
    def __new__(cls, action, *args, **kwargs):
        return Step(*args, type="Then", action=action, **kwargs)


class Do(Step):
    def __new__(cls, action, *args, **kwargs):
        return Step(*args, action=action, **kwargs)


class And(Step):
    def __new__(cls, action, *args, **kwargs):
        return Step(*args, type="And", action=action, **kwargs)


class But(Step):
    def __new__(cls, action, *args, **kwargs):
        return Step(*args, type="But", action=action, **kwargs)


KEYWORDS = ["given", "when", "then", "and", "but", "*"]


def step_deserialization_schema_selector(obj, parent_obj):
    if isinstance(obj, str):
        return StepStringSchema()

    try:
        key, *others = iter(obj.keys())
        if others:
            raise TypeError
        key = str(key).strip().lower()
    except StopIteration as e:
        raise TypeError from e

    if key in KEYWORDS:
        return StepKeywordSchema()
    elif key == "alternative":
        return AlternativeSchema()
    else:
        return StepContainerSchema()


def table_deserialization_schema_selector(obj, parent_obj):
    try:
        key, *others = iter(obj.keys())
        if others:
            raise TypeError
        key = str(key).strip().lower()
    except StopIteration as e:
        raise TypeError from e

    if key == "table":
        return TableContainerSchema()
    elif key == "join":
        return JoinSchema()
    else:
        raise TypeError


TablePolyfield = partial(
    PolyField,
    deserialization_schema_selector=table_deserialization_schema_selector,
)

StepPolyfield = partial(
    PolyField,
    deserialization_schema_selector=step_deserialization_schema_selector,
)


class StepSchema(NodeSchema):
    steps = StepPolyfield(many=True, data_key="Steps", required=False)

    action = fields.Str(required=False, data_key="Action")
    type = fields.Str(required=False, data_key="Type")
    data = TablePolyfield(many=True, data_key="Data", required=False)
    examples = TablePolyfield(many=True, data_key="Examples", required=False)

    schema_post_loader = Step.schema_post_loader()


class StepContainerSchema(Schema):
    step = fields.Nested(StepSchema, data_key="Step")

    @post_load
    def _(self, obj, *args, **kwargs):
        return obj["step"]


class StepStringSchema(StepSchema, Schema):
    @pre_load
    def convert(self, data, many, **kwargs):
        return {"Action": data}


class StepKeywordSchema(StepSchema, Schema):
    @pre_load
    def convert(self, data, many, **kwargs):
        return (lambda keyword, action: {"Action": action, "Type": keyword})(*next(iter(data.items())))


@attrs
class Alternative(ModelSchemaPostLoadable):
    steps: list[Step | Alternative] = attrib(default=Factory(list))

    @property
    def routes(self):
        yield from chain.from_iterable(map(attrgetter("routes"), self.steps))


class AlternativeSchema(Schema):
    steps = StepPolyfield(many=True, data_key="Alternative")

    schema_post_loader = Alternative.schema_post_loader()


@attrs
class Table(Node, ModelSchemaPostLoadable):
    type: str | None = attrib(default="Rowed")
    parameters: list[str] = attrib(default=Factory(list))
    values: list[list[str]] = attrib(default=Factory(list))

    @property
    def columned_values(self):
        if self.type == "Columned":
            return self.values
        else:
            return list(zip(*self.values))

    @property
    def rowed_values(self):
        if self.type == "Rowed":
            return self.values
        else:
            return list(zip(*self.values))


class TableSchema(NodeSchema):
    type = fields.Str(required=False, data_key="Type")

    parameters = fields.List(
        CastableToStrField(),
        data_key="Parameters",
    )
    values = fields.List(fields.List(CastableToStrField()), data_key="Values")

    schema_post_loader = Table.schema_post_loader()


class TableContainerSchema(Schema):
    table = fields.Nested(lambda: TableSchema(), data_key="Table")

    @post_load
    def _(self, obj, *args, **kwargs):
        return obj["table"]


@attrs
class Join(ModelSchemaPostLoadable):
    tables: list[Table] = attrib(default=Factory(list))

    __hash__ = id

    @property
    def tags(self):
        return list({*chain.from_iterable(map(attrgetter("tags"), self.tables))})

    @property
    def name(self):
        return "\n".join(filter(partial(is_not, None), reversed(list(chain(map(attrgetter("name"), self.tables))))))

    @property
    def description(self):
        return "\n".join(
            filter(
                partial(is_not, None),
                chain.from_iterable(map(deepattrgetter("description", skip_missing=True), self.tables)),
            )
        )

    @property
    def comments(self):
        return list(chain(map(attrgetter("comments"), self.tables)))

    @property
    def parameters(self):
        return list(set(chain.from_iterable(map(attrgetter("parameters"), self.tables))))

    @property
    def type(self):
        return "Rowed"

    @property
    def values(self):
        def _():
            filled_tables = list(filter(attrgetter("parameters"), self.tables))
            if filled_tables:
                filled_tables_parameters = list(chain.from_iterable(map(attrgetter("parameters"), self.tables)))
                for filled_tables_values in map(
                    lambda tables_values: list(chain.from_iterable(tables_values)),
                    product(*map(attrgetter("rowed_values"), filled_tables)),
                ):
                    if all(
                        [
                            all(
                                starmap(
                                    eq,
                                    product(
                                        [
                                            value
                                            for _parameter, value in zip(filled_tables_parameters, filled_tables_values)
                                            if parameter == _parameter
                                        ],
                                        repeat=2,
                                    ),
                                )
                            )
                            for parameter in self.parameters
                        ]
                    ):

                        def values_gen():
                            for parameter in self.parameters:
                                for _parameter, value in zip(filled_tables_parameters, filled_tables_values):
                                    if parameter == _parameter:
                                        yield value
                                        break

                        values = list(values_gen())
                        yield values
            else:
                yield from map(
                    lambda values_combination: list(chain.from_iterable(values_combination)),
                    product(*map(attrgetter("rowed_values"), self.tables)),
                )

        _values = list(_())
        return _values

    @property
    def columned_values(self):
        return list(zip(*self.values))

    @property
    def rowed_values(self):
        return self.values


class JoinSchema(Schema):
    tables = TablePolyfield(many=True, data_key="Join")

    schema_post_loader = Join.schema_post_loader()
