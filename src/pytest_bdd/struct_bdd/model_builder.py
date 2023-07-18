from itertools import filterfalse
from json import loads as json_loads
from operator import attrgetter
from typing import Any, Union, cast

from attr import attrib, attrs
from gherkin.pickles.compiler import Compiler

from messages import (  # type:ignore[attr-defined]
    DataTable,
    DocString,
    Examples,
    Feature,
    FeatureChild,
    GherkinDocument,
    KeywordType,
    Location,
    Scenario,
    Step,
    TableCell,
    TableRow,
    Tag,
    Type,
)
from pytest_bdd.model.gherkin_document import Feature as GherkinDocumentFeature
from pytest_bdd.struct_bdd.model import Join as StructJoin
from pytest_bdd.struct_bdd.model import StepPrototype as StructStep
from pytest_bdd.struct_bdd.model import Table as StructTable


@attrs
class _ASTBuilder:
    model: Any

    def build(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


@attrs
class GherkinDocumentBuilder(_ASTBuilder):
    model: StructStep = attrib()

    def build(self, id_generator):
        return GherkinDocument(
            comments=[], uri=None, feature=StepToFeatureASTBuilder(self.model).build(id_generator=id_generator)
        )

    def build_feature(self, filename, uri, id_generator):
        gherkin_document = self.build(id_generator=id_generator)
        gherkin_document.uri = uri

        gherkin_document_serialized = gherkin_document.model_dump_json(by_alias=True, exclude_none=True)

        scenarios_data = Compiler().compile(json_loads(gherkin_document_serialized))
        pickles = GherkinDocumentFeature.load_pickles(scenarios_data)

        feature = GherkinDocumentFeature(  # type: ignore[call-arg]
            gherkin_document=gherkin_document,
            uri=uri,
            pickles=pickles,
            filename=filename,
        )

        feature.fill_registry()

        return feature


@attrs
class StepToFeatureASTBuilder(_ASTBuilder):
    model: StructStep = attrib()

    def build(self, id_generator):
        return Feature(
            children=self._build_children(id_generator=id_generator),
            description=self.model.description or "",
            language="EN",
            location=Location(column=0, line=0),
            tags=[],
            name=self.model.name or "",
            keyword="Feature",
        )

    def _build_children(self, id_generator):
        def _():
            for route in self.model.routes:
                if route.steps:

                    def steps_gen(steps):
                        previous_step_keyword_type = None
                        for step in steps:
                            step_keyword_type = (
                                previous_step_keyword_type
                                if step.keyword_type is KeywordType.conjunction
                                else step.keyword_type
                            )
                            yield Step(
                                id=next(id_generator),
                                keyword=step.type if isinstance(step.type, str) else cast(Type, step.type).value,
                                location=Location(column=0, line=0),
                                text=step.action,
                                keyword_type=step_keyword_type.value,
                                **(
                                    (
                                        lambda rows: dict(
                                            data_table=DataTable(
                                                rows=rows,
                                                location=Location(column=0, line=0),  # type: ignore[call-arg]
                                            )  # type: ignore[call-arg]
                                        )
                                        if rows
                                        else {}
                                    )(
                                        [
                                            *filterfalse(
                                                lambda row: row is None,
                                                map(
                                                    lambda row_values: (
                                                        (
                                                            lambda cells: TableRow(
                                                                id=next(id_generator),
                                                                location=Location(column=0, line=0),  # type: ignore[call-arg]
                                                                cells=cells,
                                                            )  # type: ignore[call-arg]
                                                            if cells
                                                            else None
                                                        )(
                                                            [
                                                                *map(
                                                                    lambda parameter: TableCell(
                                                                        location=Location(column=0, line=0),
                                                                        value=parameter,
                                                                    ),
                                                                    row_values,
                                                                )
                                                            ]
                                                        )
                                                    ),
                                                    StructJoin(tables=step.data).rowed_values,
                                                ),
                                            )
                                        ]
                                    )
                                ),
                                **(
                                    dict(
                                        doc_string=DocString(
                                            content=step.description,
                                            delimiter="\n",
                                            location=Location(column=0, line=0),
                                        )
                                    )
                                    if step.description
                                    else dict()
                                ),
                            )
                            previous_step_keyword_type = step_keyword_type

                    steps = [*steps_gen(filter(lambda step: step.action is not None, route.steps))]

                    yield FeatureChild(
                        scenario=Scenario(
                            description=route.steps[0].description or "",
                            examples=[ExampleASTBuilder(route.example_table).build(id_generator=id_generator)]
                            if route.example_table.values
                            else [],
                            id=next(id_generator),
                            keyword="Scenario",
                            location=Location(column=0, line=0),
                            name=next(filter(bool, map(attrgetter("name"), reversed(route.steps))), ""),
                            tags=[
                                *map(
                                    lambda tag_name: Tag(
                                        id=next(id_generator),
                                        location=Location(column=0, line=0),
                                        name=tag_name,
                                    ),
                                    route.tags,
                                )
                            ],
                            steps=steps,
                        )
                    )

        return list(_())


@attrs
class ExampleASTBuilder(_ASTBuilder):
    model: Union[StructJoin, StructTable] = attrib()

    def build(self, id_generator):
        return Examples(
            description=self.model.description,
            id=next(id_generator),
            keyword="Examples",
            location=Location(column=0, line=0),
            name=self.model.name,
            table_body=[
                *map(
                    lambda row_values: TableRow(
                        id=next(id_generator),
                        location=Location(column=0, line=0),
                        cells=[
                            *map(
                                lambda parameter: TableCell(
                                    location=Location(column=0, line=0),
                                    value=str(parameter),
                                ),
                                row_values,
                            )
                        ],
                    ),
                    self.model.rowed_values,
                )
            ],
            tags=[
                *map(
                    lambda tag_name: Tag(
                        id=next(id_generator),
                        location=Location(column=0, line=0),
                        name=tag_name,
                    ),
                    self.model.tags,
                )
            ],
            table_header=TableRow(
                id=next(id_generator),
                location=Location(column=0, line=0),
                cells=[
                    *map(
                        lambda parameter: TableCell(
                            location=Location(column=0, line=0),
                            value=parameter,
                        ),
                        self.model.parameters,
                    )
                ],
            ),
        )
