import asyncio
import os
import ssl
from contextlib import suppress
from functools import partial, reduce
from itertools import filterfalse
from operator import methodcaller, truediv
from os.path import commonpath
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable, Iterable, Optional, Protocol, Tuple, Type, Union, cast, runtime_checkable
from urllib.parse import urljoin

import aiohttp
import certifi
from _pytest.config import Config
from attr import Factory, attrib, attrs
from pydantic import ValidationError

from messages import Source  # type:ignore[attr-defined]
from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import get_config_root_path
from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.model import Feature, Pickle
from pytest_bdd.scenario import Args
from pytest_bdd.utils import PytestBDDIdGeneratorHandler, is_local_url


@runtime_checkable
class ScenarioLocatorFeatureResolver(Protocol):
    def resolve_features(
        self, config: Union[Config, PytestBDDIdGeneratorHandler]
    ) -> Iterable[Tuple[Feature, Source]]:  # pragma: no cover
        ...


@runtime_checkable
class ScenarioLocatorResolver(Protocol):
    def resolve(
        self, config: Union[Config, PytestBDDIdGeneratorHandler]
    ) -> Iterable[Tuple[Feature, Pickle, Source]]:  # pragma: no cover
        ...


@attrs
class ScenarioLocatorFilterMixin(ScenarioLocatorFeatureResolver, ScenarioLocatorResolver):
    filter_: Optional[Callable[[Config, Feature, Pickle], Tuple[Feature, Pickle]]] = attrib(default=None, kw_only=True)

    def filter_scenarios(self, feature, config):
        return (
            (feature, pickle)
            for pickle in feature.pickles
            if self.filter_ is None or self.filter_(config, feature, pickle)
        )  # type: ignore

    def resolve(self, config: Config):
        for feature, feature_data in self.resolve_features(config):
            for _, pickle in self.filter_scenarios(feature, config):
                yield feature, pickle, feature_data


@attrs
class UrlScenarioLocator(ScenarioLocatorFilterMixin):
    url_paths = attrib()
    encoding = attrib()
    features_base_url = attrib()
    mimetype = attrib()
    parser_type = attrib()
    parse_args = attrib()

    async def fetch(self, session: aiohttp.ClientSession, url):
        sslcontext = ssl.create_default_context(cafile=certifi.where())
        async with session.get(url, ssl=sslcontext) as response:
            return response.content_type, await response.text(encoding=self.encoding)

    async def fetch_all(self, urls):
        async with aiohttp.ClientSession() as session:
            return await asyncio.gather(*[self.fetch(session, url) for url in urls], return_exceptions=True)

    def resolve_features(self, config: Union[Config, PytestBDDIdGeneratorHandler]):
        urls = [*filterfalse(is_local_url, self.url_paths)]
        if self.features_base_url is not None:
            urls.extend(map(partial(urljoin, f"{self.features_base_url}/"), filter(is_local_url, self.url_paths)))
        if not urls:
            return
        loop = asyncio.new_event_loop()
        responses = loop.run_until_complete(self.fetch_all(urls))

        # Wait 250 ms for the underlying SSL connections to close
        loop.run_until_complete(asyncio.sleep(0.250))
        loop.close()

        hook_handler = cast(Config, config).hook
        encoding = self.encoding

        for url, response in zip(urls, responses):
            if isinstance(response, Exception):
                continue

            mimetype, feature_content = response

            if self.mimetype is not None:
                mimetype = self.mimetype

                if isinstance(mimetype, Mimetype):
                    mimetype = mimetype.value

            if self.parser_type is None:
                parser_type = hook_handler.pytest_bdd_get_parser(
                    config=config,
                    mimetype=mimetype,
                )
            else:
                parser_type = self.parser_type

            if parser_type is None:
                break

            parser = parser_type(id_generator=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator)

            try:
                filename = None
                with NamedTemporaryFile(mode="w", delete=False) as f:
                    filename = f.name
                    f.write(feature_content)

                feature, feature_data = parser.parse(
                    config,
                    Path(filename),
                    url,
                    *self.parse_args.args,
                    **{**dict(encoding=encoding), **self.parse_args.kwargs},
                )
                try:
                    yield feature, Source(uri=url, data=feature_data, media_type=mimetype)  # type: ignore[call-arg] # migration to pydantic2
                except ValidationError as e:
                    # Workaround because of https://github.com/cucumber/messages/issues/161
                    yield feature, None
            finally:
                if filename is not None:
                    with suppress(Exception):
                        os.unlink(filename)


@attrs
class FileScenarioLocator(ScenarioLocatorFilterMixin):
    feature_paths = attrib(default=Factory(list))
    encoding = attrib(default="utf-8")
    features_base_dir: Optional[Union[str, Path]] = attrib(default=None)
    mimetype: Optional[str] = attrib(default=None)
    parser_type: Optional[Type[ParserProtocol]] = attrib(default=None)
    parse_args: Args = attrib(default=Factory(lambda: Args((), {})))

    def _resolve_features_base_dir(self, config: Union[Config, PytestBDDIdGeneratorHandler]):
        try:
            if self.features_base_dir is None:
                features_base_dir = cast(Config, config).getini("bdd_features_base_dir")
            else:
                features_base_dir = self.features_base_dir
        except (ValueError, KeyError):
            features_base_dir = get_config_root_path(cast(Config, config))
        else:
            if callable(features_base_dir):
                features_base_dir = features_base_dir(config)

            features_base_dir = (get_config_root_path(cast(Config, config)) / Path(features_base_dir)).resolve()

        return features_base_dir

    def _gen_feature_paths(self, features_base_dir):
        for feature_pathlike in self.feature_paths:
            if isinstance(feature_pathlike, Path):
                feature_path = features_base_dir / feature_pathlike
                if feature_path.is_dir():
                    yield from filter(methodcaller("is_file"), feature_path.glob("**/*"))
                else:
                    yield feature_path
            else:
                try:
                    yield from filter(methodcaller("is_file"), features_base_dir.glob(str(feature_pathlike)))
                except IndexError:
                    yield from filter(methodcaller("is_file"), features_base_dir.glob("**/*"))

    @staticmethod
    def _build_file_uri(features_base_dir: Path, feature_path: Path):
        if feature_path.is_absolute():
            try:
                common_path = Path(commonpath([feature_path, features_base_dir]))
            except ValueError:
                rel_feature_path = feature_path
            else:
                sub_levels = len(features_base_dir.relative_to(common_path).parts)
                sub_path = reduce(truediv, [".."] * sub_levels, Path())
                rel_feature_path = sub_path / feature_path.relative_to(common_path)
        else:
            rel_feature_path = feature_path

        return "file:" + str(rel_feature_path.as_posix())

    def resolve_features(self, config: Union[Config, PytestBDDIdGeneratorHandler]):
        features_base_dir = self._resolve_features_base_dir(config)
        already_resolved_feature_paths = set()

        for feature_path in self._gen_feature_paths(features_base_dir=features_base_dir):
            feature_path_key = str(feature_path)
            if feature_path_key in already_resolved_feature_paths:
                break

            uri = self._build_file_uri(features_base_dir, feature_path)
            already_resolved_feature_paths.add(feature_path_key)
            hook_handler = cast(Config, config).hook
            encoding = self.encoding

            if self.mimetype is None:
                media_type = hook_handler.pytest_bdd_get_mimetype(config=config, path=feature_path)
            else:
                media_type = self.mimetype

            if self.parser_type is None:
                parser_type = hook_handler.pytest_bdd_get_parser(
                    config=config,
                    mimetype=media_type,
                )
            else:
                parser_type = self.parser_type

            if parser_type is None:
                break

            parser = parser_type(id_generator=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator)

            feature, feature_data = parser.parse(
                config,
                feature_path,
                uri,
                *self.parse_args.args,
                **{**dict(encoding=encoding), **self.parse_args.kwargs},
            )
            try:
                yield feature, Source(uri=uri, data=feature_data, media_type=media_type)  # type: ignore[call-arg] # migration to pydantic2
            except ValidationError as e:
                # Workaround because of https://github.com/cucumber/messages/issues/161
                yield feature, None
