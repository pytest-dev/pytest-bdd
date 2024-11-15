"""Step parsers."""

from __future__ import annotations

import abc
import re as base_re
from typing import TYPE_CHECKING, Any, TypeVar, cast

import parse as base_parse
from _pytest.config import Config
from parse_type import cfparse as base_cfparse

if TYPE_CHECKING:
    from _pytest.config.argparsing import Parser as PytestArgParser


def add_options(parser: PytestArgParser) -> None:
    """Add pytest-bdd options."""
    group = parser.getgroup("bdd")
    group.addoption(
        "--bdd-default-parser",
        action="store",
        default=None,
        help="Set the default step parser type (e.g. string, parse, re, cfparse).",
    )


def configure(config: Config):
    """Set the default parser in pytest configuration."""
    try:
        parser_type = config.getoption("bdd_default_parser") or config.getini("bdd_default_parser")
    except ValueError:
        # If the option is not found, fallback to the default parser
        parser_type = "string"

    config._bdd_default_parser = parser_type


class StepParser(abc.ABC):
    """Parser of the individual step."""

    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    def parse_arguments(self, name: str) -> dict[str, Any] | None:
        """Get step arguments from the given step name.

        :return: `dict` of step arguments
        """
        ...

    @abc.abstractmethod
    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        ...


class re(StepParser):
    """Regex step parser."""

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Compile regex."""
        super().__init__(name)
        self.regex = base_re.compile(self.name, *args, **kwargs)

    def parse_arguments(self, name: str) -> dict[str, str] | None:
        """Get step arguments.

        :return: `dict` of step arguments
        """
        match = self.regex.fullmatch(name)
        if match is None:
            return None
        return match.groupdict()

    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        return bool(self.regex.fullmatch(name))


class parse(StepParser):
    """parse step parser."""

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Compile parse expression."""
        super().__init__(name)
        self.parser = base_parse.compile(self.name, *args, **kwargs)

    def parse_arguments(self, name: str) -> dict[str, Any]:
        """Get step arguments.

        :return: `dict` of step arguments
        """
        return cast(dict[str, Any], self.parser.parse(name).named)

    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False


class cfparse(parse):
    """cfparse step parser."""

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Compile parse expression."""
        super(parse, self).__init__(name)
        self.parser = base_cfparse.Parser(self.name, *args, **kwargs)


class string(StepParser):
    """Exact string step parser."""

    def parse_arguments(self, name: str) -> dict:
        """No parameters are available for simple string step.

        :return: `dict` of step arguments
        """
        return {}

    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        return self.name == name


TStepParser = TypeVar("TStepParser", bound=StepParser)


def get_parser(step_name: str | StepParser, config: Config | None = None) -> StepParser:
    """Get parser by given name."""
    if isinstance(step_name, StepParser):
        return step_name

    default_parser = getattr(config, "_bdd_default_parser", "string") if config else "string"

    parser_classes = {
        "string": string,
        "parse": parse,
        "re": re,
        "cfparse": cfparse,
    }

    parser_cls = parser_classes.get(default_parser, string)
    return parser_cls(step_name)
