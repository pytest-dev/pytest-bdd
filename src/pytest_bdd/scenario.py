import collections
from enum import Enum
from pathlib import Path
from typing import Callable, Iterable, Optional, Type, Union

from pytest import mark

from pytest_bdd.compatibility.parser import ParserProtocol
from pytest_bdd.compatibility.pytest import Parser
from pytest_bdd.mimetypes import Mimetype
from pytest_bdd.utils import compose, make_python_name

Args = collections.namedtuple("Args", ["args", "kwargs"])


def add_options(parser: Parser):
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd", "Scenario")
    group.addoption(
        "--disable-feature-autoload",
        action="store_false",
        dest="feature_autoload",
        default=None,
        help="Turn off feature files autoload",
    )
    parser.addini(
        "disable_feature_autoload",
        default=False,
        type="bool",
        help="Turn off feature files autoload",
    )


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
    feature_name: Optional[Union[Path, str]] = None,
    scenario_name: Optional[str] = None,
    encoding: str = "utf-8",
    features_base_dir: Optional[Union[Path, str]] = None,
    features_base_url=None,
    features_path_type: Optional[Union[FeaturePathType, str]] = FeaturePathType.PATH,
    features_mimetype: Optional[Mimetype] = None,
    return_test_decorator=True,
    parser_type: Optional[Type[ParserProtocol]] = None,
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
    :param features_path_type: If feature path is not absolute helps to select if filepath or url will be used
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
    *feature_paths: Union[Path, str],
    filter_: Optional[Union[str, Callable]] = None,
    return_test_decorator=False,
    encoding: str = "utf-8",
    features_base_dir: Optional[Union[Path, str]] = None,
    features_base_url: Optional[str] = None,
    features_path_type: Optional[Union[FeaturePathType, str]] = FeaturePathType.PATH,
    features_mimetype: Optional[Mimetype] = None,
    parser_type: Optional[Type[ParserProtocol]] = None,
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
    :param features_path_type: If feature path is not absolute helps to select if filepath or url will be used
    :param features_mimetype: Helps to select appropriate parser if non-standard file extension is used
    :param return_test_decorator; Return test decorator or generated test
    :param parser_type: Parser used to parse feature-like file
    :param parse_args: args consumed by parser during parsing
    :param return_test_decorator; Return test decorator or generated test
    :param locators: Feature locators to load Features; Could be custom
    """
    if features_base_dir and features_base_url:
        raise ValueError('Both "features_base_dir" and "features_base_url" were specified')
    if features_base_dir:
        features_path_type = FeaturePathType.PATH
    elif features_base_url:
        features_path_type = FeaturePathType.URL

    decorator = compose(
        mark.pytest_bdd_scenario,
        mark.usefixtures("feature", "scenario", "feature_source"),
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
