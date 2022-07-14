from __future__ import annotations

from itertools import count
from operator import attrgetter
from typing import Any

from attr import Factory, attrib, attrs

import pytest_bdd.ast as ast
from pytest_bdd.struct_bdd.model import Join, Step, Table


@attrs
class _ASTBuilder:
    model: Any
    id_generator = attrib(default=Factory(lambda: map(str, count())), kw_only=True)

    def build(self, *args, **kwargs):  # pragma: no cover
        raise NotImplementedError


@attrs
class DocumentASTBuilder(_ASTBuilder):
    model: Step = attrib()

    def build(self):
        return ast.AST(
            gherkin_document=ast.GherkinDocument(comments=[], uri=None).setattrs(
                feature=StepToFeatureASTBuilder(self.model, id_generator=self.id_generator).build()
            )
        )


@attrs
class StepToFeatureASTBuilder(_ASTBuilder):
    model: Step = attrib()

    def build(self):
        return ast.Feature(
            children=self._build_children(),
            description=self.model.description or "",
            language="EN",
            location=ast.Location(column=0, line=0),
            tags=[],
            name=self.model.name or "",
        ).setattrs(keyword="Feature")

    def _build_children(self):
        def _():
            for route in self.model.routes:
                if route.steps:
                    yield ast.NodeContainerChild().setattrs(
                        scenario=ast.Scenario(
                            description=route.steps[0].description or "",
                            examples=[ExampleASTBuilder(route.example_table, id_generator=self.id_generator).build()]
                            if route.example_table.values
                            else [],
                            identifier=next(self.id_generator),
                            keyword="Scenario",
                            location=ast.Location(column=0, line=0),
                            name=next(filter(bool, map(attrgetter("name"), reversed(route.steps))), ""),
                            tags=[
                                *map(
                                    lambda tag_name: ast.Tag(
                                        identifier=next(self.id_generator),
                                        location=ast.Location(column=0, line=0),
                                        name=tag_name,
                                    ),
                                    route.tags,
                                )
                            ],
                            steps=[
                                *map(
                                    lambda step: ast.Step(
                                        identifier=next(self.id_generator),
                                        keyword=step.type,
                                        location=ast.Location(column=0, line=0),
                                        text=step.action,
                                        keyword_type=step.keyword_type,
                                    ).setattrs(
                                        data_table=ast.DataTable(
                                            rows=[
                                                *map(
                                                    lambda row_values: ast.TableRow(
                                                        identifier=next(self.id_generator),
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
                                                    Join(tables=step.data).rowed_values,
                                                )
                                            ],
                                            location=ast.Location(column=0, line=0),
                                        ),
                                        **(
                                            {
                                                "doc_string": ast.DocString(
                                                    content=step.description,
                                                    delimiter="\n",
                                                    location=ast.Location(column=0, line=0),
                                                )
                                            }
                                            if step.description
                                            else {}
                                        ),
                                    ),
                                    filter(lambda step: step.action is not None, route.steps),
                                )
                            ],
                        )
                    )

        return list(_())


@attrs
class ExampleASTBuilder(_ASTBuilder):
    model: Table | Join = attrib()

    def build(self):
        return ast.Example(
            description=self.model.description,
            identifier=next(self.id_generator),
            keyword="Examples",
            location=ast.Location(column=0, line=0),
            name=self.model.name,
            table_body=[
                *map(
                    lambda row_values: ast.TableRow(
                        identifier=next(self.id_generator),
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
                        identifier=next(self.id_generator),
                        location=ast.Location(column=0, line=0),
                        name=tag_name,
                    ),
                    self.model.tags,
                )
            ],
        ).setattrs(
            table_header=ast.ExampleTableHeader(
                identifier=next(self.id_generator),
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
