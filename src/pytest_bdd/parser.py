from __future__ import annotations

import linecache
from functools import partial
from itertools import filterfalse
from operator import contains, methodcaller
from os.path import relpath
from pathlib import Path
from typing import Callable, cast

from attr import attrib, attrs
from attr._make import Factory
from gherkin.ast_builder import AstBuilder
from gherkin.errors import CompositeParserException
from gherkin.parser import Parser as CucumberIOBaseParser  # type: ignore[import]
from gherkin.pickles.compiler import Compiler as PicklesCompiler

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Config
from pytest_bdd.compatibility.struct_bdd import STRUCT_BDD_INSTALLED
from pytest_bdd.exceptions import FeatureError
from pytest_bdd.model import Feature
from pytest_bdd.model.messages import MediaType, Message, Source
from pytest_bdd.utils import IdGenerator, PytestBDDIdGeneratorHandler

if STRUCT_BDD_INSTALLED:  # pragma: no cover
    from pytest_bdd.struct_bdd.parser import StructBDDParser

    assert StructBDDParser  # type: ignore[truthy-function]


@attrs
class GlobMixin:
    glob: Callable[..., list[str | Path]] = attrib(default=methodcaller("glob", "*.feature"), kw_only=True)


class ASTBuilderMixin:
    def build_feature(self, gherkin_document_raw_dict, filename: str, id_generator) -> Feature:
        gherkin_document = Feature.load_gherkin_document(gherkin_document_raw_dict)

        pickles_data = PicklesCompiler(id_generator=id_generator).compile(gherkin_document_raw_dict)
        pickles = Feature.load_pickles(pickles_data)

        feature = Feature(  # type: ignore[call-arg]
            gherkin_document=gherkin_document,
            uri=gherkin_document.uri,
            pickles=pickles,
            filename=filename,
        )

        return feature


@attrs
class GherkinParser(CucumberIOBaseParser, ASTBuilderMixin, GlobMixin, ParserProtocol):
    id_generator = attrib(default=Factory(IdGenerator))

    def __attrs_post_init__(self):
        CucumberIOBaseParser.__init__(self, ast_builder=AstBuilder(id_generator=self.id_generator))

    @classmethod
    def parse(cls, config: Config | PytestBDDIdGeneratorHandler, path: Path, uri: str, *args, **kwargs) -> Feature:
        parser = cls(id_generator=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator)
        encoding = kwargs.pop("encoding", "utf-8")
        with path.open(mode="r", encoding=encoding) as feature_file:
            feature_file_data = feature_file.read()

        if ".md" in path.suffixes:
            media_type = MediaType.text_x_cucumber_gherkin_markdown
        else:
            media_type = MediaType.text_x_cucumber_gherkin_plain

        cast(Config, config).hook.pytest_bdd_message(
            config=config, message=Message(source=Source(uri=uri, data=feature_file_data, media_type=media_type))
        )

        try:
            gherkin_document_raw_dict = CucumberIOBaseParser.parse(
                parser, token_scanner_or_str=feature_file_data, *args, **kwargs
            )
        except CompositeParserException as e:
            raise FeatureError(
                e.args[0],
                e.errors[0].location["line"],
                linecache.getline(str(path), e.errors[0].location["line"]).rstrip("\n"),
                uri,
            ) from e

        gherkin_document_raw_dict["uri"] = uri

        feature = parser.build_feature(
            gherkin_document_raw_dict,
            filename=str(path.as_posix()),
            id_generator=getattr(config, "pytest_bdd_id_generator", IdGenerator()),
        )

        cast(Config, config).hook.pytest_bdd_message(
            config=config, message=Message(gherkin_document=feature.gherkin_document)
        )
        for pickle in feature.pickles:
            cast(Config, config).hook.pytest_bdd_message(config=config, message=Message(pickle=pickle))

        return feature

    def get_from_paths(self, config: Config, paths: list[Path], **kwargs) -> list[Feature]:
        """Get features for given paths."""
        seen_names: set[Path] = set()
        features: list[Feature] = []
        features_base_dir = kwargs.pop("features_base_dir", Path.cwd())
        if not features_base_dir.is_absolute():
            features_base_dir = Path.cwd() / features_base_dir

        for rel_path in map(Path, paths):
            path = rel_path if rel_path.is_absolute() else Path(features_base_dir) / rel_path

            file_paths = list(map(Path, self.glob(path))) if path.is_dir() else [Path(path)]

            features.extend(
                map(
                    lambda path: self.parse(
                        config, path, "file:" + relpath(str(path), str(features_base_dir)), **kwargs
                    ),
                    filterfalse(partial(contains, seen_names), file_paths),
                )
            )

            for file_path in file_paths:
                if file_path not in seen_names:
                    seen_names.add(path)

        return sorted(features, key=lambda feature: feature.name or feature.filename)
