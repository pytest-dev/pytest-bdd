"""StepHandler parsers."""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from operator import attrgetter
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import Any, Iterable, cast

import parse as base_parse
import parse_type.cfparse as base_cfparse
from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry

from pytest_bdd.typing import Protocol, runtime_checkable
from pytest_bdd.utils import singledispatchmethod, stringify


@runtime_checkable
class StepParserProtocol(Protocol):
    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any] | None:
        ...  # pragma: no cover

    def is_matching(self, name: str) -> bool:
        ...  # pragma: no cover

    def __str__(self) -> str:
        ...  # pragma: no cover


class StepParser(StepParserProtocol, metaclass=ABCMeta):
    """Parser of the individual step."""

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


class re(StepParser):
    """Regex step parser."""

    @singledispatchmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    @__init__.register
    def _(self, pattern: str, *args: Any, **kwargs: Any) -> None:
        """Compile regex."""
        self.pattern = pattern
        self.regex = re_compile(self.pattern, *args, **kwargs)

    @__init__.register
    def _(self, pattern: _RePattern):
        """Compile regex."""
        self.pattern = pattern.pattern
        self.regex = pattern

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
        return stringify(self.pattern)


class parse(StepParser):
    """parse step parser."""

    @singledispatchmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    @__init__.register
    def _(self, format: str, *args: Any, builder=base_parse.compile, **kwargs: Any) -> None:
        """Compile parse expression."""
        self.format = format
        self.parser = builder(self.format, *args, **kwargs)

    @__init__.register
    def _(self, format: base_parse.Parser):
        self.format = format._format
        self.parser = format

    @classmethod
    def cfparse(cls, *args, **kwargs):
        kwargs.setdefault("builder", base_cfparse.Parser)
        return cls(*args, **kwargs)

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
        return str(self.format)


cfparse = parse.cfparse


class string(StepParser):
    """Exact string step parser."""

    def __init__(self, name: str | bytes) -> None:
        """Stringify"""
        self.name = stringify(name)

    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any]:
        """No parameters are available for simple string step.

        :return: `dict` of step arguments
        """
        return {}

    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        return bool(self.name == name)


class cucumber_expression(StepParser):
    @singledispatchmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    @__init__.register
    def _(self, expression: str, parameter_type_registry: ParameterTypeRegistry = ParameterTypeRegistry()):
        self.pattern = expression
        self.expression = CucumberExpression(expression, parameter_type_registry=parameter_type_registry)

    @__init__.register
    def _(self, expression: CucumberExpression):
        self.pattern = expression.expression
        self.expression = expression

    def is_matching(self, name: str) -> bool:
        return bool(self.expression.match(name))

    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any] | None:
        return dict(zip(anonymous_group_names or [], map(attrgetter("value"), self.expression.match(name))))

    def __str__(self):
        return str(self.pattern)


def get_parser(parserlike: str | StepParser | StepParserProtocol) -> StepParser:
    """Get parser by given name.

    :param parserlike: name of the step to parse

    :return: step parser object
    :rtype: StepParser
    """

    if isinstance(parserlike, StepParserProtocol):
        parser = cast(StepParser, parserlike)
    elif isinstance(parserlike, _RePattern):
        parser = re(parserlike)
    elif isinstance(parserlike, base_parse.Parser):
        parser = parse(parserlike)
    elif isinstance(parserlike, CucumberExpression):
        parser = cucumber_expression(parserlike)
    else:
        parser = cfparse(parserlike)

    return parser
