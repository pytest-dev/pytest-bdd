"""Feature.

The way of describing the behavior is based on Gherkin language

Syntax example:

    Feature: Articles
        Scenario: Publishing the article
            Given I'm an author user
            And I have an article
            When I go to the article page
            And I press the publish button
            Then I should not see the error message

            # Note: will query the database
            And the article should be published

:note: The "#" symbol is used for comments.
:note: There are no multiline steps, the description of the step must fit in
one line.
"""
from __future__ import annotations

from itertools import chain
from textwrap import dedent
from typing import cast

from attr import Factory, attrib, attrs
from gherkin.errors import CompositeParserException  # type: ignore[import]
from gherkin.pickles.compiler import Compiler  # type: ignore[import]

from pytest_bdd.compatibility.functools import singledispatchmethod
from pytest_bdd.const import TAG_PREFIX
from pytest_bdd.model.messages import Background, Examples
from pytest_bdd.model.messages import Feature as FeatureMessage
from pytest_bdd.model.messages import GherkinDocument, Pickle, PickleStep, Rule, Scenario, Step, TableRow, Tag
from pytest_bdd.model.scenario import UserStep
from pytest_bdd.utils import _itemgetter, deepattrgetter


@attrs
class Feature:
    gherkin_document: GherkinDocument = attrib()
    uri = attrib()
    filename: str = attrib()

    registry: dict = attrib(default=Factory(dict))
    pickles: list[Pickle] = attrib(default=Factory(list))

    def __attrs_post_init__(self):
        self.fill_registry()

    @staticmethod
    def load_pickles(scenarios_data) -> list[Pickle]:
        return [*map(Pickle.parse_obj, scenarios_data)]

    def fill_registry(self):
        self.registry.update(self.get_child_ids_gen(self.gherkin_document.feature))

    @classmethod
    def get_child_ids_gen(cls, obj):
        if isinstance(obj, FeatureMessage):
            yield from chain.from_iterable(
                map(
                    cls.get_child_ids_gen,
                    chain(
                        obj.tags,
                        chain.from_iterable(
                            map(
                                lambda child: filter(None, [child.rule, child.background, child.scenario]), obj.children
                            )
                        ),
                    ),
                )
            )
        elif isinstance(obj, Tag):
            yield obj.id, obj
        elif isinstance(obj, Rule):
            yield obj.id, obj
            yield from chain.from_iterable(
                map(
                    cls.get_child_ids_gen,
                    chain(
                        obj.tags,
                        chain.from_iterable(
                            map(
                                lambda child: filter(
                                    None,
                                    [
                                        # Check why we don't support nested Rules
                                        # child.rule,
                                        child.background,
                                        child.scenario,
                                    ],
                                ),
                                obj.children,
                            )
                        ),
                    ),
                )
            )
        elif isinstance(obj, Background):
            yield obj.id, obj
            yield from chain.from_iterable(map(cls.get_child_ids_gen, obj.steps))
        elif isinstance(obj, Scenario):
            yield obj.id, obj
            yield from chain.from_iterable(
                map(
                    cls.get_child_ids_gen,
                    chain(
                        obj.tags,
                        obj.steps,
                        obj.examples,
                    ),
                )
            )
        elif isinstance(obj, Examples):
            yield obj.id, obj
            yield from chain.from_iterable(
                map(cls.get_child_ids_gen, chain(obj.tags, [obj.table_header], obj.table_body))
            )
        elif isinstance(obj, TableRow):
            yield obj.id, obj
        elif isinstance(obj, Step):
            yield obj.id, obj

    load_gherkin_document = staticmethod(GherkinDocument.parse_obj)

    @property
    def name(self) -> str | None:
        if self.gherkin_document.feature is not None:
            return self.gherkin_document.feature.name
        else:
            return None

    @property
    def rel_filename(self):
        file_schema = "file"
        if self.uri.startswith(file_schema):
            return self.uri[len(file_schema) + 1 :]
        else:
            return None

    @property
    def line_number(self):
        return self.gherkin_document.feature.location.line

    @property
    def description(self):
        return dedent(self.gherkin_document.feature.description)

    @property
    def tag_names(self):
        return sorted(map(lambda tag: tag.name.lstrip(TAG_PREFIX), self.gherkin_document.feature.tags))

    def build_pickle_table_rows_breadcrumb(self, pickle):
        table_rows_lines = ",".join(
            map(
                lambda row: f"line: {deepattrgetter('location.line', default=-1)(row)[0]}",
                self._get_pickle_ast_table_rows(pickle),
            )
        )
        return f"[table_rows:[{table_rows_lines}]]" if table_rows_lines else ""

    def _get_pickle_ast_table_rows(self, pickle):
        return list(filter(lambda node: type(node) is TableRow, self._get_linked_ast_nodes(pickle)))

    def _get_linked_ast_nodes(self, obj):
        return _itemgetter(
            *((obj.ast_node_id,) if hasattr(obj, "ast_node_id") else ()),
            *getattr(obj, "ast_node_ids", ()),
        )(self.registry)

    def _get_pickle_tag_names(self, pickle: Pickle):
        return sorted(map(lambda tag: tag.name.lstrip(TAG_PREFIX), pickle.tags))

    def _get_pickle_ast_scenario(self, pickle: Pickle) -> Scenario:
        return cast(Scenario, next(filter(lambda node: type(node) is Scenario, self._get_linked_ast_nodes(pickle))))

    def _get_pickle_line_number(self, pickle: Pickle):
        return self._get_pickle_ast_scenario(pickle).location.line

    def _get_pickle_step_ast_step(self, pickle_step: PickleStep):
        return cast(Step, next(filter(lambda node: type(node) is Step, self._get_linked_ast_nodes(pickle_step)), None))

    @singledispatchmethod
    def _get_step_keyword(self, step: PickleStep):
        return self._get_pickle_step_ast_step(step).keyword.strip()

    @_get_step_keyword.register
    def _(self, step: UserStep):
        return step.keyword

    @singledispatchmethod
    def _get_step_prefix(self, step: PickleStep):
        return self._get_step_keyword(step).lower()

    @_get_step_prefix.register
    def _(self, step: UserStep):
        return step.prefix

    @singledispatchmethod
    def _get_step_line_number(self, step: PickleStep):
        return self._get_pickle_step_ast_step(step).location.line

    @_get_step_line_number.register
    def _(self, step: UserStep):
        return step.line_number

    @singledispatchmethod
    def _get_step_doc_string(self, step: PickleStep):
        return self._get_pickle_step_ast_step(step).doc_string

    @_get_step_doc_string.register
    def _(self, step: UserStep):
        return step.doc_string

    @singledispatchmethod
    def _get_step_data_table(self, step: PickleStep):
        return self._get_pickle_step_ast_step(step).data_table

    @_get_step_data_table.register
    def _(self, step: UserStep):
        return step.data_table
