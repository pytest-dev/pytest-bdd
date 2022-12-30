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

import collections
from functools import reduce
from operator import truediv
from os.path import commonpath
from pathlib import Path
from typing import Callable, Iterable, Sequence, cast

import pytest
from attr import Factory, attrib, attrs

from pytest_bdd.model import Feature
from pytest_bdd.model.messages import Pickle
from pytest_bdd.parser import GherkinParser
from pytest_bdd.typing.parser import ParserProtocol
from pytest_bdd.typing.pytest import Config, Parser
from pytest_bdd.utils import PytestBDDIdGeneratorHandler, make_python_name

Args = collections.namedtuple("Args", ["args", "kwargs"])


def add_options(parser: Parser):
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Scenario")
    group.addoption(
        "--feature-autoload",
        action="store_true",
        dest="feature_autoload",
        default=None,
        help="Turn on feature files autoload",
    )
    parser.addini(
        "feature_autoload",
        default=False,
        type="bool",
        help="Turn on feature files autoload",
    )


@attrs
class FileScenarioLocator:
    feature_paths = attrib(default=Factory(list))
    filter_: Callable[[Config, Feature, Pickle], tuple[Feature, Pickle]] | None = attrib(default=None)
    encoding = attrib(default="utf-8")
    features_base_dir: str | Path | None = attrib(default=None)
    parser_type: type[ParserProtocol] = attrib(default=GherkinParser)
    parse_args: Args = attrib(default=Factory(lambda: Args((), {})))

    def resolve(self, config: Config | PytestBDDIdGeneratorHandler):
        try:
            if self.features_base_dir is None:
                features_base_dir = cast(Config, config).getini("bdd_features_base_dir")
            else:
                features_base_dir = self.features_base_dir
        except (ValueError, KeyError):
            features_base_dir = cast(Config, config).rootpath
        if callable(features_base_dir):
            features_base_dir = features_base_dir(config)
        features_base_dir = (Path(cast(Config, config).rootpath) / Path(features_base_dir)).resolve()

        already_resolved = set()

        parser = self.parser_type(id_generator=cast(PytestBDDIdGeneratorHandler, config).pytest_bdd_id_generator)

        def feature_paths_gen():
            for feature_path in map(Path, self.feature_paths):
                if feature_path.is_dir():
                    yield from iter(parser.glob(feature_path))
                else:
                    yield feature_path

        for feature_path in feature_paths_gen():
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

            uri = str(rel_feature_path.as_posix())
            absolute_feature_path = (Path(features_base_dir) / rel_feature_path).resolve()

            if absolute_feature_path not in already_resolved:
                already_resolved.add(absolute_feature_path)

                feature = parser.parse(
                    config,
                    absolute_feature_path,
                    uri,
                    *self.parse_args.args,
                    **{**dict(encoding=self.encoding), **self.parse_args.kwargs},
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


def scenario(
    feature_name: Path | str = Path(),
    scenario_name: str | None = None,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    return_test_decorator=True,
    parser: type[ParserProtocol] | None = None,
    parse_args=Args((), {}),
    locators=(),
):
    """
    Scenario decorator.

    :param feature_name: Feature file name. Absolute or relative to the configured feature base path.
    :param scenario_name: Scenario name.
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param return_test_decorator; Return test decorator or generated test
    :param parser: Parser used to parse feature-like file
    :param parse_args: args consumed by parser during parsing
    """
    return _scenarios(
        feature_paths=[feature_name],
        filter_=scenario_name,
        encoding=encoding,
        features_base_dir=features_base_dir,
        return_test_decorator=return_test_decorator,
        locators=locators,
        parser_type=parser,
        parse_args=parse_args,
    )


def scenarios(
    *feature_paths: Path | str,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    return_test_decorator=False,
    parser: type[ParserProtocol] | None = None,
    parse_args=Args((), {}),
    locators=(),
):
    """
    Scenario decorator.

    :param feature_paths: Features file names. Absolute or relative to the configured feature base path.
    :param encoding: Feature file encoding.
    :param features_base_dir: Feature base directory from where features will be searched
    :param return_test_decorator; Return test decorator or generated test
    """
    return _scenarios(
        feature_paths=feature_paths,
        filter_=None,
        encoding=encoding,
        features_base_dir=features_base_dir,
        return_test_decorator=return_test_decorator,
        parser_type=parser,
        parse_args=parse_args,
        locators=locators,
    )


def _scenarios(
    feature_paths: Sequence[Path | str] | None = None,
    feature_urls: Sequence[str] = (),
    filter_: str | Callable | None = None,
    return_test_decorator=True,
    encoding: str = "utf-8",
    features_base_dir: Path | str | None = None,
    features_base_url: str | None = None,
    parser_type: type[ParserProtocol] | None = None,
    parse_args=Args((), {}),
    locators=(),
):
    if parser_type is None:
        parser_type = GherkinParser

    if isinstance(filter_, str):
        updated_filter = lambda config, feature, scenario: scenario.name == filter_
    elif callable(filter_):
        updated_filter = filter_
    else:
        updated_filter = None

    def compose(*funcs):
        return reduce(lambda f, g: lambda *args, **kwargs: f(g(*args, **kwargs)), funcs)

    decorator = compose(
        pytest.mark.pytest_bdd_scenario,
        pytest.mark.usefixtures("feature", "scenario"),
        pytest.mark.scenarios(
            feature_paths=feature_paths,
            feature_urls=feature_urls,
            filter_=updated_filter,
            encoding=encoding,
            features_base_dir=features_base_dir,
            features_base_url=features_base_url,
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
