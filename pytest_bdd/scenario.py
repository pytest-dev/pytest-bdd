"""Scenario implementation.

The pytest will collect the test case and the steps will be executed
line by line.

Example:

test_publish_article = scenario(
    feature_name="publish_article.feature",
    scenario_name="Publishing the article",
)
"""
from __future__ import annotations

import asyncio
import collections
import os
import ssl
from contextlib import suppress
from enum import Enum
from functools import partial, reduce
from operator import methodcaller, truediv
from os.path import commonpath
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable, Iterable, cast
from urllib.parse import urljoin

import aiohttp
import certifi
from attr import Factory, attrib, attrs
from pytest import mark

from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.model import Feature
from pytest_bdd.model.messages import Pickle
from pytest_bdd.parser import GherkinParser
from pytest_bdd.typing.parser import ParserProtocol
from pytest_bdd.typing.pytest import PYTEST61, Config, Parser
from pytest_bdd.utils import PytestBDDIdGeneratorHandler, compose, make_python_name

Args = collections.namedtuple("Args", ["args", "kwargs"])


def add_options(parser: Parser):
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Scenario")
    group.addoption(
        "--disable-feature-autoload",
        action="store_false",
        dest="feature_autoload",
        default=True,
        help="Turn off feature files autoload",
    )
    parser.addini(
        "disable_feature_autoload",
        default=True,
        type="bool",
        help="Turn off feature files autoload",
    )


@attrs
class UrlScenarioLocator:
    url_paths = attrib()
    filter_ = attrib()
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

    def resolve(self, config: Config | PytestBDDIdGeneratorHandler):
        urls = list(
            self.url_paths
            if self.features_base_url is None
            else map(partial(urljoin, self.features_base_url), self.url_paths)
        )
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

            raw_mimetype, feature_content = response
            try:
                mimetype = Mimetype(raw_mimetype)
            except:
                mimetype = None

            if self.mimetype is not None:
                mimetype = self.mimetype

            if isinstance(mimetype, str):
                mimetype = Mimetype(mimetype)

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

                feature = parser.parse(
                    config,
                    Path(filename),
                    url,
                    *self.parse_args.args,
                    **{**dict(encoding=encoding), **self.parse_args.kwargs},
                )

                for pickle in feature.pickles:
                    if self.filter_ is None or self.filter_(config, feature, pickle):  # type: ignore
                        yield feature, pickle
            finally:
                if filename is not None:
                    with suppress(Exception):
                        os.unlink(filename)


@attrs
class FileScenarioLocator:
    feature_paths = attrib(default=Factory(list))
    filter_: Callable[[Config, Feature, Pickle], tuple[Feature, Pickle]] | None = attrib(default=None)
    encoding = attrib(default="utf-8")
    features_base_dir: str | Path | None = attrib(default=None)
    mimetype: str | None = attrib(default=None)
    parser_type: type[ParserProtocol] | None = attrib(default=GherkinParser)
    parse_args: Args = attrib(default=Factory(lambda: Args((), {})))

    @staticmethod
    def _resolve_pytest_rootpath(config: Config | PytestBDDIdGeneratorHandler) -> Path:
        return Path(getattr(cast(Config, config), "rootpath" if PYTEST61 else "rootdir"))

    def _resolve_features_base_dir(self, config: Config | PytestBDDIdGeneratorHandler):
        try:
            if self.features_base_dir is None:
                features_base_dir = cast(Config, config).getini("bdd_features_base_dir")
            else:
                features_base_dir = self.features_base_dir
        except (ValueError, KeyError):
            features_base_dir = self._resolve_pytest_rootpath(config)
        else:
            if callable(features_base_dir):
                features_base_dir = features_base_dir(config)

            features_base_dir = (self._resolve_pytest_rootpath(config) / Path(features_base_dir)).resolve()

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

    def resolve(self, config: Config | PytestBDDIdGeneratorHandler):
        features_base_dir = self._resolve_features_base_dir(config)
        already_resolved_feature_paths = set()

        for feature_path in self._gen_feature_paths(features_base_dir=features_base_dir):

            feature_path_key = str(feature_path)
            if feature_path_key in already_resolved_feature_paths:
                break

            uri = self._build_file_uri(features_base_dir, feature_path)
            already_resolved_feature_paths.add(feature_path_key)
            hook_handler = cast(Config, config).hook

            if self.parser_type is None:
                if self.mimetype is None:
                    calculated_pytest_mimetype = hook_handler.pytest_bdd_get_mimetype(config=config, path=feature_path)
                    if calculated_pytest_mimetype is None:
                        mimetype, encoding = self.encoding, self.mimetype
                    else:
                        mimetype, encoding = calculated_pytest_mimetype
                else:
                    mimetype, encoding = self.encoding, self.mimetype

                if encoding is None:
                    encoding = self.encoding

                parser_type = hook_handler.pytest_bdd_get_parser(
                    config=config,
                    mimetype=mimetype,
                )
            else:
                parser_type = self.parser_type
                encoding = self.encoding

            if parser_type is None:
                break

            parser = parser_type(id_generator=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator)

            feature = parser.parse(
                config,
                feature_path,
                uri,
                *self.parse_args.args,
                **{**dict(encoding=encoding), **self.parse_args.kwargs},
            )

            for pickle in feature.pickles:
                if self.filter_ is None or self.filter_(config, feature, pickle):  # type: ignore
                    yield feature, pickle


def get_python_name_generator(name: str) -> Iterable[str]:
    """Generate a sequence of suitable python names out of given arbitrary string name."""
    python_name = make_python_name(name)
    suffix = ""
    index = 0

    def get_name() -> str:
        return "_".join(filter(bool, ["test", python_name, suffix]))

    while True:
        yield get_name()
        index += 1
        suffix = f"{index}"


test_names = get_python_name_generator("")


class FeaturePathType(Enum):
    PATH = "path"
    URL = "url"
    UNDEFINED = "undefined"


def scenario(
    feature_name: Path | str | None = None,
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url=None,
    features_path_type: FeaturePathType | str | None = None,
    features_mimetype: Mimetype | None = None,
    return_test_decorator=True,
    parser_type: type[ParserProtocol] | None = None,
    parse_args=Args((), {}),
    locators=(),
):
    """
    Scenario decorator.

    :param feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param scenario_name: Scenario name.
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param features_base_url: Feature base url from where features will be loaded
    :param features_path_type: If feature path is not absolute helps to select if filepath o url will be used
    :param features_mimetype: Helps to select appropriate parser if non-standard file extension is used
    :param return_test_decorator; Return test decorator or generated test
    :param parser_type: Parser used to parse feature-like file
    :param parse_args: args consumed by parser during parsing
    :param locators: Feature locators to load Features; Could be custom
    """
    return scenarios(
        *([feature_name] if feature_name is not None else []),
        filter_=scenario_name,
        encoding=encoding,
        features_base_dir=features_base_dir,
        features_base_url=features_base_url,
        features_path_type=features_path_type,
        features_mimetype=features_mimetype,
        return_test_decorator=return_test_decorator,
        locators=locators,
        parser_type=parser_type,
        parse_args=parse_args,
    )


def scenarios(
    *feature_paths: Path | str,
    filter_: str | Callable | None = None,
    return_test_decorator=False,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    features_path_type: FeaturePathType | str | None = None,
    features_mimetype: Mimetype | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args=Args((), {}),
    locators=(),
):
    """
    Function to bind feature files to pytest runtime

    :param feature_paths: Features file names. Absolute or relative to the configured feature base path.
    :param filter_: Callable to filter scenarios
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param features_base_url: Feature base url from where features will be loaded
    :param features_path_type: If feature path is not absolute helps to select if filepath o url will be used
    :param features_mimetype: Helps to select appropriate parser if non-standard file extension is used
    :param return_test_decorator; Return test decorator or generated test
    :param parser_type: Parser used to parse feature-like file
    :param parser_type: Parser used to parse feature-like file
    :param parse_args: args consumed by parser during parsing
    :param return_test_decorator; Return test decorator or generated test
    :param locators: Feature locators to load Features; Could be custom
    """

    decorator = compose(
        mark.pytest_bdd_scenario,
        mark.usefixtures("feature", "scenario"),
        mark.scenarios(
            *feature_paths,
            filter_=filter_,
            encoding=encoding,
            features_base_dir=features_base_dir,
            features_base_url=features_base_url,
            features_path_type=features_path_type,
            features_mimetype=features_mimetype,
            parser_type=parser_type,
            parse_args=parse_args,
            locators=locators,
        ),
    )

    if return_test_decorator:
        return decorator
    else:

        @decorator
        def test():
            ...

        test.__name__ = next(iter(test_names))

        return test
