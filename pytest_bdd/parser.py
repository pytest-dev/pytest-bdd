from __future__ import annotations

import linecache
from functools import partial
from itertools import filterfalse
from operator import contains, methodcaller
from pathlib import Path
from typing import Callable

from attr import attrib, attrs
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser  # type: ignore[import]
from gherkin.pickles.compiler import Compiler

from pytest_bdd.exceptions import FeatureError
from pytest_bdd.model.feature import Feature as FeatureModel
from pytest_bdd.typing.parser import ParserProtocol
from pytest_bdd.typing.struct_bdd import STRUCT_BDD_INSTALLED

if STRUCT_BDD_INSTALLED:  # pragma: no cover
    from pytest_bdd.struct_bdd.parser import StructBDDParser

    assert StructBDDParser


@attrs
class GlobMixin:
    glob: Callable[..., list[str | Path]] = attrib(default=methodcaller("rglob", "*.feature"), kw_only=True)


class ASTBuilderMixin:
    def build_feature(self, gherkin_ast_data, filename: str) -> FeatureModel:
        gherkin_ast = FeatureModel.load_ast(gherkin_ast_data)

        scenarios_data = Compiler().compile(gherkin_ast_data["gherkinDocument"])
        scenarios = FeatureModel.load_scenarios(scenarios_data)

        instance = FeatureModel(  # type: ignore[call-arg]
            gherkin_ast=gherkin_ast,
            uri=gherkin_ast.gherkin_document.uri,
            scenarios=scenarios,
            filename=filename,
        )

        for scenario in scenarios:
            scenario.bind_feature(instance)

        return instance


@attrs
class GherkinParser(CucumberIOBaseParser, ASTBuilderMixin, GlobMixin, ParserProtocol):
    ast_builder = attrib(default=None)

    def __attrs_post_init__(self):
        CucumberIOBaseParser.__init__(self, ast_builder=self.ast_builder)

    def parse(self, path: Path, uri: str, *args, **kwargs) -> FeatureModel:
        encoding = kwargs.pop("encoding", "utf-8")
        with path.open(mode="r", encoding=encoding) as feature_file:
            feature_file_data = feature_file.read()
        try:
            ast_data = CucumberIOBaseParser.parse(self, token_scanner_or_str=feature_file_data, *args, **kwargs)
        except CompositeParserException as e:
            raise FeatureError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(path), e.errors[0].location["line"]).rstrip("\n"),
                uri,
            ) from e

        ast_data["uri"] = uri
        document_ast_data = {"gherkinDocument": ast_data}

        return self.build_feature(document_ast_data, filename=str(path.as_posix()))

    def get_from_paths(self, paths: list[Path], **kwargs) -> list[FeatureModel]:
        """Get features for given paths.

        :param list paths: `list` of paths (file or dirs)

        :return: `list` of `Feature` objects.
        """
        seen_names: set[Path] = set()
        features: list[FeatureModel] = []
        features_base_dir = kwargs.pop("features_base_dir", Path.cwd())
        if not features_base_dir.is_absolute():
            features_base_dir = Path.cwd() / features_base_dir

        for rel_path in map(Path, paths):
            path = rel_path if rel_path.is_absolute() else Path(features_base_dir) / rel_path

            file_paths = list(map(Path, self.glob(path))) if path.is_dir() else [Path(path)]

            features.extend(
                map(
                    lambda path: self.parse(path, str(path.relative_to(features_base_dir).as_posix()), **kwargs),
                    filterfalse(partial(contains, seen_names), file_paths),
                )
            )

            for file_path in file_paths:
                if file_path not in seen_names:
                    seen_names.add(path)

        return sorted(features, key=lambda feature: feature.name or feature.filename)
