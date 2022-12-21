from __future__ import annotations

from itertools import count, filterfalse
from operator import attrgetter
from typing import Any

from attr import Factory, attrib, attrs

import pytest_bdd.ast as ast
from pytest_bdd.model.messages import KeywordType
from pytest_bdd.struct_bdd.model import Join, Step, Table

# TODO rework to use pydantic models instead


@attrs
class _ASTBuilder:
    model: Any

    def build(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


@attrs
class GherkinDocumentBuilder(_ASTBuilder):
    model: Step = attrib()

    def build(self, id_generator):
        return ast.GherkinDocument(comments=[], uri=None).setattrs(
            feature=StepToFeatureASTBuilder(self.model).build(id_generator=id_generator)
        )


@attrs
class StepToFeatureASTBuilder(_ASTBuilder):
    model: Step = attrib()

    def build(self, id_generator):
        return ast.Feature(
            children=self._build_children(id_generator=id_generator),
            description=self.model.description or "",
            language="EN",
            location=ast.Location(column=0, line=0),
            tags=[],
            name=self.model.name or "",
        ).setattrs(keyword="Feature")

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
                            yield ast.Step(
                                identifier=next(id_generator),
                                keyword=step.type,
                                location=ast.Location(column=0, line=0),
                                text=step.action,
                                keyword_type=step_keyword_type.value,
                            ).setattrs(
                                **(
                                    (
                                        lambda rows: dict(
                                            data_table=ast.DataTable(
                                                rows=rows,
                                                location=ast.Location(column=0, line=0),  # type: ignore[call-arg]
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
                                                            lambda cells: ast.TableRow(
                                                                identifier=next(id_generator),
                                                                location=ast.Location(column=0, line=0),  # type: ignore[call-arg]
                                                                cells=cells,
                                                            )  # type: ignore[call-arg]
                                                            if cells
                                                            else None
                                                        )(
                                                            [
                                                                *map(
                                                                    lambda parameter: ast.TableCell(
                                                                        location=ast.Location(column=0, line=0),
                                                                        value=parameter,
                                                                    ),
                                                                    row_values,
                                                                )
                                                            ]
                                                        )
                                                    ),
                                                    Join(tables=step.data).rowed_values,
                                                ),
                                            )
                                        ]
                                    )
                                ),
                                **(
                                    dict(
                                        doc_string=ast.DocString(
                                            content=step.description,
                                            delimiter="\n",
                                            location=ast.Location(column=0, line=0),
                                        )
                                    )
                                    if step.description
                                    else dict()
                                ),
                            )
                            previous_step_keyword_type = step_keyword_type

                    steps = [*steps_gen(filter(lambda step: step.action is not None, route.steps))]

                    yield ast.NodeContainerChild().setattrs(
                        scenario=ast.Scenario(
                            description=route.steps[0].description or "",
                            examples=[ExampleASTBuilder(route.example_table).build(id_generator=id_generator)]
                            if route.example_table.values
                            else [],
                            identifier=next(id_generator),
                            keyword="Scenario",
                            location=ast.Location(column=0, line=0),
                            name=next(filter(bool, map(attrgetter("name"), reversed(route.steps))), ""),
                            tags=[
                                *map(
                                    lambda tag_name: ast.Tag(
                                        identifier=next(id_generator),
                                        location=ast.Location(column=0, line=0),
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
    model: Table | Join = attrib()

    def build(self, id_generator):
        return ast.Example(
            description=self.model.description,
            identifier=next(id_generator),
            keyword="Examples",
            location=ast.Location(column=0, line=0),
            name=self.model.name,
            table_body=[
                *map(
                    lambda row_values: ast.TableRow(
                        identifier=next(id_generator),
                        location=ast.Location(column=0, line=0),
                        cells=[
                            *map(
                                lambda parameter: ast.TableCell(
                                    location=ast.Location(column=0, line=0),
                                    value=parameter,
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
                    lambda tag_name: ast.Tag(
                        identifier=next(id_generator),
                        location=ast.Location(column=0, line=0),
                        name=tag_name,
                    ),
                    self.model.tags,
                )
            ],
        ).setattrs(
            table_header=ast.ExampleTableHeader(
                identifier=next(id_generator),
                location=ast.Location(column=0, line=0),
                cells=[
                    *map(
                        lambda parameter: ast.TableCell(
                            location=ast.Location(column=0, line=0),
                            value=parameter,
                        ),
                        self.model.parameters,
                    )
                ],
            ),
        )