"""StepHandler parsers."""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import Any, cast

import parse as base_parse
import parse_type.cfparse as base_cfparse

from pytest_bdd.typing import Protocol, runtime_checkable


@runtime_checkable
class StepParserProtocol(Protocol):
    name: Any

    def parse_arguments(self, name: str) -> dict[str, Any] | None:
        ...

    def is_matching(self, name: str) -> bool:
        ...


class StepParser(StepParserProtocol, metaclass=ABCMeta):
    """Parser of the individual step."""

    def __init__(self, name: Any) -> None:
        self.name = name

    @abstractmethod
    def parse_arguments(self, name: str) -> dict[str, Any] | None:
        """Get step arguments from the given step name.

        :return: `dict` of step arguments
        """
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        raise NotImplementedError()  # pragma: no cover


class _CommonRe(StepParser):
    regex: _RePattern

    def parse_arguments(self, name):
        return self.regex.match(name).groupdict()

    def is_matching(self, name):
        return bool(self.regex.match(name))


class _re(_CommonRe):
    def __init__(self, name):
        """Compile regex."""
        super().__init__(name.pattern)
        self.regex = name


class re(_CommonRe):
    """Regex step parser."""

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Compile regex."""
        super().__init__(name)
        self.regex = re_compile(self.name, *args, **kwargs)


class _CommonParse(StepParser):
    parser: base_parse.Parser

    def parse_arguments(self, name: str) -> dict[str, Any] | None:
        return cast(dict, self.parser.parse(name).named)

    def is_matching(self, name):
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False


class _parse(_CommonParse):
    def __init__(self, name: base_parse.Parser):
        super().__init__(name._format)
        self.parser = name


class parse(_CommonParse):
    """parse step parser."""

    def __init__(self, name: str, *args: Any, **kwargs: Any) -> None:
        """Compile parse expression."""
        super().__init__(name)
        self.parser = base_parse.compile(self.name, *args, **kwargs)


class cfparse(_CommonParse):
    """cfparse step parser."""

    def __init__(self, name, *args, **kwargs):
        """Stringify"""
        name = str(name, **({"encoding": "utf-8"} if isinstance(name, bytes) else {}))
        super().__init__(name)
        """Compile parse expression."""
        self.parser = base_cfparse.Parser(self.name, *args, **kwargs)


class string(StepParser):
    """Exact string step parser."""

    def __init__(self, name: str | bytes) -> None:
        """Stringify"""
        name = str(name, **({"encoding": "utf-8"} if isinstance(name, bytes) else {}))
        super().__init__(name)

    def parse_arguments(self, name: str) -> dict[str, Any]:
        """No parameters are available for simple string step.

        :return: `dict` of step arguments
        """
        return {}

    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        return bool(self.name == name)


def get_parser(parserlike: str | StepParser | StepParserProtocol) -> StepParser:
    """Get parser by given name.

    :param parserlike: name of the step to parse

    :return: step parser object
    :rtype: StepArgumentParser
    """

    if isinstance(parserlike, StepParserProtocol):
        return cast(StepParser, parserlike)
    elif isinstance(parserlike, _RePattern):
        return _re(parserlike)
    elif isinstance(parserlike, base_parse.Parser):
        return _parse(parserlike)
    else:
        return cfparse(parserlike)
