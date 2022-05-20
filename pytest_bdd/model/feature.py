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

from textwrap import dedent
from typing import cast

from attr import Factory, attrib, attrs
from gherkin.errors import CompositeParserException  # type: ignore[import]
from gherkin.pickles.compiler import Compiler  # type: ignore[import]

from pytest_bdd.ast import AST, ASTSchema
from pytest_bdd.const import STEP_PREFIXES, TAG
from pytest_bdd.model.scenario import Scenario, ScenarioSchema


@attrs
class Feature:
    gherkin_ast: AST = attrib()
    uri = attrib()
    filename: str = attrib()

    scenarios: list[Scenario] = attrib(default=Factory(list))

    @staticmethod
    def load_scenarios(scenarios_data) -> list[Scenario]:
        return [ScenarioSchema().load(data=scenario_datum, unknown="RAISE") for scenario_datum in scenarios_data]

    @staticmethod
    def load_ast(ast_data) -> AST:
        return cast(AST, ASTSchema().load(data=ast_data, unknown="RAISE"))

    @property
    def name(self) -> str:
        return self.gherkin_ast.gherkin_document.feature.name

    @property
    def rel_filename(self):
        return self.uri

    @property
    def line_number(self):
        return self.gherkin_ast.gherkin_document.feature.location.line

    @property
    def description(self):
        return dedent(self.gherkin_ast.gherkin_document.feature.description)

    @property
    def tag_names(self):
        return sorted(
            map(lambda tag: tag.name.lstrip(STEP_PREFIXES[TAG]), self.gherkin_ast.gherkin_document.feature.tags)
        )

    def decompose(self):
        for scenario in self.scenarios:
            scenario.decompose()

    def compose(self):
        for scenario in self.scenarios:
            scenario.bind_feature(self)
            scenario.bind_steps()
