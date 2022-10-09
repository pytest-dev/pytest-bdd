"""StepHandler parsers."""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import Any, Iterable, cast

import parse as base_parse
import parse_type.cfparse as base_cfparse

from pytest_bdd.typing import Protocol, runtime_checkable


@runtime_checkable
class StepParserProtocol(Protocol):
    name: Any

    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any] | None:
        ...  # pragma: no cover

    def is_matching(self, name: str) -> bool:
        ...  # pragma: no cover

    def __str__(self) -> str:
        ...  # pragma: no cover


class StepParser(StepParserProtocol, metaclass=ABCMeta):
    """Parser of the individual step."""

    def __init__(self, name: Any) -> None:
        self.name = name

    @abstractmethod
    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any] | None:
        """Get step arguments from the given step name.

        :return: `dict` of step arguments
        """
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def __str__(self) -> str:
        """Match given name with the step name."""
        raise NotImplementedError()  # pragma: no cover


class _CommonRe(StepParser):
    regex: _RePattern

    def parse_arguments(
        self,
        name,
        anonymous_group_names: Iterable[str] | None = None,
    ):
        match = cast(Match, self.regex.match(name))  # Can't be None because is already matched
        group_dict = match.groupdict()
        if anonymous_group_names is not None:
            groups_count = len(match.groups())
            named_group_spans = [*map(match.span, group_dict.keys())]
            group_dict.update(
                {
                    anonymous_group_name: name[slice(*anonymous_group_span)]
                    for anonymous_group_name, anonymous_group_span in zip(
                        anonymous_group_names,
                        filter(lambda span: span not in named_group_spans, map(match.span, range(1, groups_count + 1))),
                    )
                }
            )

        return group_dict

    def is_matching(self, name):
        return bool(self.regex.match(name))

    def __str__(self):
        return str(self.name)


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

    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any] | None:
        match = self.parser.parse(name)
        group_dict = cast(dict, match.named)
        if anonymous_group_names is not None:
            group_dict.update(dict(zip(anonymous_group_names, match.fixed)))
        return group_dict

    def is_matching(self, name):
        try:
            return bool(self.parser.parse(name))
        except ValueError:
            return False

    def __str__(self):
        return str(self.name)


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

    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any]:
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
    :rtype: StepParser
    """

    if isinstance(parserlike, StepParserProtocol):
        return cast(StepParser, parserlike)
    elif isinstance(parserlike, _RePattern):
        return _re(parserlike)
    elif isinstance(parserlike, base_parse.Parser):
        return _parse(parserlike)
    else:
        return cfparse(parserlike)
