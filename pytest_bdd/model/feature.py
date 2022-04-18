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

import linecache
from pathlib import Path
from textwrap import dedent
from typing import cast

from attr import Factory, attrib, attrs
from gherkin.errors import CompositeParserException  # type: ignore[import]
from gherkin.parser import Parser  # type: ignore[import]
from gherkin.pickles.compiler import Compiler  # type: ignore[import]

from pytest_bdd.ast import AST, ASTSchema
from pytest_bdd.const import STEP_PREFIXES, TAG
from pytest_bdd.exceptions import FeatureError
from pytest_bdd.model.scenario import Scenario, ScenarioSchema


@attrs
class Feature:
    gherkin_ast: AST = attrib()
    uri = attrib()
    filename: str = attrib()

    scenarios: list[Scenario] = attrib(default=Factory(list))

    @classmethod
    def get_from_path(cls, features_base_dir: Path | str, filename: Path | str, encoding: str = "utf-8") -> Feature:
        absolute_feature_path = (Path(features_base_dir) / filename).resolve()
        _filename = Path(filename)
        relative_posix_feature_path = (
            _filename.relative_to(features_base_dir) if _filename.is_absolute() else _filename
        ).as_posix()

        uri = str(relative_posix_feature_path)

        with absolute_feature_path.open(mode="r", encoding=encoding) as feature_file:
            feature_file_data = feature_file.read()

        try:
            gherkin_ast_data = Parser().parse(feature_file_data)
        except CompositeParserException as e:
            raise FeatureError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(absolute_feature_path), e.errors[0].location["line"]).rstrip("\n"),
                uri,
            ) from e
        gherkin_ast_data["uri"] = uri

        gherkin_ast = cls.load_ast({"gherkinDocument": gherkin_ast_data})

        scenarios_data = Compiler().compile(gherkin_ast_data)
        scenarios = cls.load_scenarios(scenarios_data)

        instance = cls(  # type: ignore[call-arg]
            gherkin_ast=gherkin_ast,
            uri=uri,
            scenarios=scenarios,
            filename=str(absolute_feature_path.as_posix()),
        )

        for scenario in scenarios:
            scenario.bind_feature(instance)

        return instance

    @classmethod
    def get_from_paths(cls, paths: list[Path], **kwargs) -> list[Feature]:
        """Get features for given paths.

        :param list paths: `list` of paths (file or dirs)

        :return: `list` of `Feature` objects.
        """
        seen_names = set()
        features: list[Feature] = []
        features_base_dir = kwargs.pop("features_base_dir", Path.cwd())
        for path in map(Path, paths):
            if path not in seen_names:
                seen_names.add(path)
                if path.is_dir():
                    _path = path if path.is_absolute() else Path(features_base_dir) / path
                    features.extend(cls.get_from_paths(list(_path.rglob("*.feature")), **kwargs))
                else:
                    feature = cls.get_from_path(features_base_dir, path, **kwargs)
                    features.append(feature)
        return sorted(features, key=lambda feature: feature.name or feature.filename)

    @staticmethod
    def load_scenarios(scenarios_data) -> list[Scenario]:
        return [ScenarioSchema().load(data=scenario_datum, unknown="RAISE") for scenario_datum in scenarios_data]

    @staticmethod
    def load_ast(ast_data) -> AST:
        return cast(AST, ASTSchema().load(data=ast_data, unknown="RAISE"))

    # region TODO: Deprecated
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
    def registry(self):
        return self.gherkin_ast.registry

    @property
    def tag_names(self):
        return sorted(
            map(lambda tag: tag.name.lstrip(STEP_PREFIXES[TAG]), self.gherkin_ast.gherkin_document.feature.tags)
        )

    # endregion
