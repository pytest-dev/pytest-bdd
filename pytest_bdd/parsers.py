"""StepHandler parsers."""
from __future__ import annotations

from abc import ABCMeta, abstractmethod
from functools import partial
from itertools import filterfalse
from operator import attrgetter, contains, methodcaller
from re import Match
from re import Pattern as _RePattern
from re import compile as re_compile
from typing import Any, Iterable, cast

import parse as base_parse
import parse_type.cfparse as base_cfparse
from cucumber_expressions.argument import Argument as CucumberExpressionArgument
from cucumber_expressions.expression import CucumberExpression
from cucumber_expressions.parameter_type_registry import ParameterTypeRegistry
from cucumber_expressions.regular_expression import RegularExpression as CucumberRegularExpression

from pytest_bdd.compatibility import Protocol, runtime_checkable
from pytest_bdd.model.messages import ExpressionType
from pytest_bdd.utils import StringableProtocol, singledispatchmethod, stringify


class ParserBuildValueError(ValueError):
    ...


@runtime_checkable
class StepParserProtocol(Protocol):
    type: ExpressionType = ExpressionType.pytest_bdd_other_expression

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

    @classmethod
    def build(cls, parserlike: str | bytes | StepParser | StepParserProtocol) -> StepParser:

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
        elif isinstance(parserlike, CucumberRegularExpression):
            parser = cucumber_regular_expression(parserlike)
        else:
            parser = heuristic(parserlike)

        return parser


class re(StepParser):
    """Regex step parser."""

    type = ExpressionType.pytest_bdd_regular_expression

    @singledispatchmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()  # pragma: no cover

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
            group_dict.update(
                zip(
                    anonymous_group_names,
                    map(
                        lambda span: name[slice(*span)],  # type: ignore[no-any-return] # https://github.com/python/mypy/issues/9590
                        filterfalse(
                            partial(contains, [*map(match.span, group_dict.keys())]),
                            map(match.span, range(1, len(match.groups()) + 1)),
                        ),
                    ),
                )
            )

        return group_dict

    def is_matching(self, name):
        return bool(self.regex.fullmatch(name))

    def __str__(self):
        return stringify(self.pattern)


class parse(StepParser):
    """parse step parser."""

    type = ExpressionType.pytest_bdd_parse_expression

    @singledispatchmethod
    def __init__(self, format, *args, **kwargs):
        if isinstance(format, (StringableProtocol, str, bytes)):
            self.__init_stringable__(format, *args, **kwargs)
        else:
            raise ParserBuildValueError(f"Unable build parser for format {format}")  # pragma: no cover

    def __init_stringable__(
        self, format: StringableProtocol | str | bytes, *args: Any, builder=base_parse.compile, **kwargs: Any
    ) -> None:
        self.format = stringify(format)
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


class cfparse(parse):
    """cfparse step parser."""

    type = ExpressionType.pytest_bdd_cfparse_expression

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("builder", base_cfparse.Parser)
        super().__init__(*args, **kwargs)


class string(StepParser):
    """Exact string step parser."""

    type = ExpressionType.pytest_bdd_string_expression

    def __init__(self, name: StringableProtocol | str | bytes) -> None:
        self.name = stringify(name)

    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any]:
        """No parameters are available for simple string step.

        :return: `dict` of step arguments
        """
        return {}

    def is_matching(self, name: str) -> bool:
        """Match given name with the step name."""
        return bool(self.name == name)

    def __str__(self):
        return self.name


@runtime_checkable
class _CucumberExpressionProtocol(Protocol):
    def match(self, text: str) -> list[CucumberExpressionArgument] | None:
        ...  # pragma: no cover


class _CucumberExpression(StepParser):
    pattern: str
    expression: _CucumberExpressionProtocol

    def is_matching(self, name: str) -> bool:
        return bool(self.expression.match(name))

    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any] | None:
        return dict(zip(anonymous_group_names or [], map(attrgetter("value"), self.expression.match(name) or [])))

    def __str__(self):
        return str(self.pattern)


class cucumber_expression(_CucumberExpression):
    type = ExpressionType.cucumber_expression

    @singledispatchmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()  # pragma: no cover

    @__init__.register
    def _(self, expression: str, parameter_type_registry: ParameterTypeRegistry = ParameterTypeRegistry()):
        self.pattern = expression
        self.expression = CucumberExpression(expression, parameter_type_registry=parameter_type_registry)

    @__init__.register
    def _(self, expression: CucumberExpression):
        self.pattern = expression.expression
        self.expression = expression


class cucumber_regular_expression(_CucumberExpression):
    type = ExpressionType.regular_expression

    @singledispatchmethod
    def __init__(self, *args, **kwargs):
        raise NotImplementedError()  # pragma: no cover

    @__init__.register
    def _(self, expression: str, parameter_type_registry: ParameterTypeRegistry = ParameterTypeRegistry()):
        self.pattern = expression
        self.expression = CucumberRegularExpression(expression, parameter_type_registry=parameter_type_registry)

    @__init__.register
    def _(self, expression: CucumberRegularExpression):
        self.pattern = expression.expression_regexp.pattern
        self.expression = expression


class heuristic(StepParser):
    type = ExpressionType.pytest_bdd_heuristic_expression

    def __init__(self, format):
        if isinstance(format, (StringableProtocol, str, bytes)):
            format = stringify(format)
        self.format = format

        # Rework to exception groups after python 3.10 end of support
        e_cause = None
        try:
            self.string_parser = string(format)
        except Exception as e:
            e_cause = e
            self.string_parser = None

        try:
            self.cucumber_expression_parser = cucumber_expression(format)
        except Exception as e:
            e.__cause__, e_cause = e_cause, e
            self.cucumber_expression_parser = None

        try:
            self.cfparse_parser = cfparse(format)
        except Exception as e:
            e.__cause__, e_cause = e_cause, e
            self.cfparse_parser = None

        try:
            self.re_parser = re(format)
        except Exception as e:
            e.__cause__, e_cause = e_cause, e
            self.re_parser = None

        if not any(self.parser_by_priorities):
            raise ParserBuildValueError(f"Unable build parser for format {format}") from e_cause  # pragma: no cover

    @property
    def parser_by_priorities(self) -> list[StepParser]:
        return [self.string_parser, self.cucumber_expression_parser, self.cfparse_parser, self.re_parser]

    def is_matching(self, name: str) -> bool:
        return any(map(methodcaller("is_matching", name), filter(bool, self.parser_by_priorities)))

    def parse_arguments(self, name: str, anonymous_group_names: Iterable[str] | None = None) -> dict[str, Any] | None:
        for parser in self.parser_by_priorities:
            if parser is not None and parser.is_matching(name):
                arguments = parser.parse_arguments(name, anonymous_group_names=anonymous_group_names)
                break
        else:
            arguments = None
        return arguments

    def __str__(self):
        return self.format
